import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
def process_date(date: str):
    #the date we scraped has the format 
    # Thứ tư, 6/8/2025, 00:00 (GMT+7)
    #we need to convert to 6/8/2025, 00:00
    cleaned_date = ", ".join(date.split(", ")[1:]) #-> 6/8/2025, 00:00 (GMT+7)
    cleaned_date = cleaned_date.split(" (")[0] #-> 6/8/2025, 00:00
    if not cleaned_date:
        return "UNK"
    dt = datetime.strptime(cleaned_date, "%d/%m/%Y, %H:%M")
    return dt
def get_url_content(article_url):
    try:
        response = requests.get(article_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        #get the date
        date = soup.find("span", class_ = "date")
        date_text = date.get_text(strip= True) if date else "UNK"

        #vnexpress contains the headers in the <a> in <ul class = "breadcrumb">
        breadcrumb = soup.find("ul", class_ = "breadcrumb")
        if breadcrumb:
            categories = [a.get_text(strip = True) for a in breadcrumb.find_all("a")]
            category_text = " - ".join(categories)
        else:
            category_text = "UNK"
        #get the content of the article        
        content_div = soup.find("article", class_ = "fck_detail")

        if content_div:
            paragraph = content_div.find_all("p")
            article_text = "\n".join(p.get_text(strip = True) for p in paragraph)
        else:
            article_text = "UNK"            

        return {
            "date": date_text,
            "category": category_text,
            "article_text": article_text
        }   
    
    except requests.RequestException as e:
        return f"Request Error: {e}"
def extract_author_and_content(article_text):
    if not article_text:
        return article_text, "UNK"
    lines = article_text.split("\n")
    if len(lines) > 1:
        authors = lines[-1]
        content = "\n".join(lines[:-1]).strip()
        return content, authors    
    else:
        return article_text, "UNK"

def get_articles(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    #this is the example HTML of vnexpress web:
    #<h3 class="title-news">
    #<a data-medium="Item-13" data-thumb="1" href="https://vnexpress.net/nguyen-xuan-son-nghi-het-nam-2025-4923094.html" title="Nguyễn Xuân Son nghỉ hết năm 2025">Nguyễn Xuân Son nghỉ hết năm 2025</a>
    #</h3>
    #so all the titles are belong in the <a> tag in side <h3 class = "title-news">
    titles = soup.find_all("h3", attrs= {"class": "title-news"})

    articles_data = []
    for title in titles:
        a_tag = title.find("a")
        if a_tag:
            new_title = a_tag.get_text(strip=True)
            article_url = a_tag.get("href")
            try:
                dict = get_url_content(article_url)
                date, category, article_text = dict["date"], dict["category"], dict["article_text"]
                                            
                content, author = extract_author_and_content(article_text)

                article_data = {
                    "title": new_title,
                    "date": str(process_date(date)),
                    "url": article_url,
                    "content": content,
                    "author": author,
                    "category": category
                }
                
                articles_data.append(article_data)
            except requests.RequestException as e:
                print(f"Error occurs {e}")
                continue 
    return articles_data
def write_into_json(output_filename, articles_data):
    #1. read the json file
    if os.path.exists(output_filename):
        new_scraped_articles = []
        print(f"{output_filename} is already existed")
        with open(output_filename, 'r', encoding = 'utf-8') as file:
            existed_articles = json.load(file)
        existed_url = set([article["url"] for article in existed_articles])
        #2. only added the articles that is not existed in the json file
        for article_data in articles_data:
            if article_data["url"] not in existed_url:
                new_scraped_articles.append(article_data)
        combined_articles = existed_articles + new_scraped_articles
        try:
            with open(output_filename, 'w', encoding = 'utf-8') as file:
                json.dump(combined_articles, file, ensure_ascii = False, indent = 2)
                print(f"Add {len(new_scraped_articles)} new articles into json file.")        
        except Exception as e:
            print(f"Error: {e}")
    
    else:
        try:
            with open(output_filename, "w", encoding = "utf-8") as json_file:
                json.dump(articles_data, json_file, ensure_ascii=False, indent = 2)
            print("Successfully saved scraped articles into json file.")

        except Exception as e:
            print(f"Error {e}")

if __name__ == "__main__":
    url = "https://vnexpress.net/"
    articles_data = get_articles(url)
    output_filename = "vnexpress_articles.json"
    write_into_json(output_filename, articles_data)