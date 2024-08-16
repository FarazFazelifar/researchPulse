import aiohttp
import asyncio
import sqlite3
import xml.etree.ElementTree as ET
import datetime
import spacy
import pycountry
import math

country_names = {country.name.lower(): country.name for country in pycountry.countries}
nlp = spacy.load("en_core_web_sm")

def distribute_items_geometric_minimum(total_items, rows):
    # Minimum items per row: 5% of total items, but at least 1
    min_items_per_row = 1
    r = (total_items ** (1 / (rows - 1)))

    # Initialize the list to store items per row
    items_distribution = []
    remaining_items = total_items

    for i in range(rows - 1):
        # Calculate items in the current row
        items_in_row = max(min_items_per_row, math.floor(remaining_items / r ** (rows - 1 - i)))
        items_distribution.append(items_in_row)
        remaining_items -= items_in_row

    # Add remaining items to the last row
    items_distribution.append(remaining_items)

    return items_distribution

def extract_country(place):
    doc = nlp(place)
    for entity in doc.ents:
        if entity.label_ == "GPE":  # GPE (Geopolitical Entity) is usually a country, city, or place
            return entity.text
    return 'N/A'

async def search_europe_pmc(session, query, max_results=50, sort_by="", start_year=1900, end_year=datetime.datetime.now().year):
    base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    
    items_per_year = distribute_items_geometric_minimum(max_results, rows=end_year- start_year + 1)
    years = range(start_year, end_year + 1)
    
    results = []
    
    for i in range(len(years)):
        params = {
            "query": f"(PUB_YEAR:{years[i]}) AND ({query})",
            "format": "xml",
            "resultType": "core",
            "pageSize": items_per_year[i],
            "sort": sort_by,
        }
        
        try:
            async with session.get(base_url, params=params) as response:
                if response.status != 200:
                    print(f"Error: HTTP {response.status}")
                    return []

                xml_content = await response.text()
                root = ET.fromstring(xml_content)

                for result in root.findall(".//result"):
                    title = result.find("title").text if result.find("title") is not None else "N/A"
                    abstract = result.find("abstractText").text if result.find("abstractText") is not None else "N/A"
                    authors = ", ".join([author.find("fullName").text for author in result.findall(".//authorList/author") if author.find("fullName") is not None])
                    
                    journal = result.find("journalTitle").text if result.find("journalTitle") is not None else "N/A"
                    if journal == "N/A":
                        journal_info = result.find("journalInfo")
                        if journal_info is not None:
                            journal_title = journal_info.find("journal/title")
                            if journal_title is not None:
                                journal = journal_title.text

                    pub_date = result.find("firstPublicationDate")
                    year = "N/A"
                    month = "N/A"
                    if pub_date is not None and pub_date.text:
                        try:
                            date_obj = datetime.datetime.strptime(pub_date.text, "%Y-%m-%d")
                            year = str(date_obj.year)
                            month = date_obj.strftime("%B")  # Full month name
                        except ValueError:
                            year = pub_date.text[:4]

                    doi = result.find("doi").text if result.find("doi") is not None else "N/A"
                    citations = result.find("citedByCount").text if result.find("citedByCount") is not None else "0"
                    
                    country = "N/A"
                    affiliations = result.findall(".//affiliation")
                    for affiliation in affiliations:
                        if affiliation is not None and affiliation.text:
                            parts = affiliation.text.split(',')
                            if len(parts) > 1:
                                country = parts[-1].strip()
                                break

                    results.append({
                        "title": title,
                        "abstract": abstract,
                        "authors": authors,
                        "journal": journal,
                        "year": year,
                        "month": month,
                        "country": extract_country(country),
                        "doi": doi,
                        "citations": int(citations),
                        "api_source": "Europe PMC"
                    })
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return []

    print(f"Number of results found: {len(results)}")
    return results



def save_to_sql(data, db_name="articles.db", table_name="articles"):
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        
        c.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        create_table_query = """
        CREATE TABLE articles (
            title TEXT,
            abstract TEXT,
            authors TEXT,
            journal TEXT,
            year TEXT,
            month TEXT,
            country TEXT,
            doi TEXT,
            citations INTEGER,
            api_source TEXT
        )
        """
        c.execute(create_table_query)
        
        for row in data:
            placeholders = ", ".join("?" for _ in row)
            insert_query = f"INSERT INTO {table_name} ({', '.join(row.keys())}) VALUES ({placeholders})"
            c.execute(insert_query, list(row.values()))
        
        conn.commit()
        print(f"Data saved to {db_name} in table {table_name}.")
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        if conn:
            conn.close()

async def main(query, max_results=50, sort_by="CITED desc", start_date="2000-01-01", end_date="2024-12-30"):
    async with aiohttp.ClientSession() as session:
        results = await search_europe_pmc(session, query, max_results=max_results, sort_by=sort_by, start_year=start_date, end_year=end_date)

        if results:
            save_to_sql(results)
        else:
            print("No results found or an error occurred.")

if __name__ == "__main__":
    query = input("Enter your search query: ")
    max_results = int(input("Enter the number of results to retrieve: "))
    sort_by = input("Enter sort order (e.g., 'cited desc', 'date desc'): ")
    start_date = int(input("Enter start year: "))
    end_date = int(input("Enter end date year: "))
    asyncio.run(main(query, max_results, sort_by, start_date, end_date))