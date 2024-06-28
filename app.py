from flask import Flask, request, jsonify, render_template
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import requests
from typing import List

app = Flask(__name__)

# Initialize the conversational pipeline with attention mask and pad token ID
model_name = "microsoft/DialoGPT-medium"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

class Book:
    def __init__(self, title: str, authors: List[str], rating: float):
        self.title = title
        self.authors = authors
        self.rating = rating

# Function to generate a response
def generate_response(input_text, history=[]):
    new_user_input_ids = tokenizer.encode(input_text + tokenizer.eos_token, return_tensors='pt')
    bot_input_ids = torch.cat([torch.LongTensor(history), new_user_input_ids], dim=-1)
    history = bot_input_ids.tolist()

    response_ids = model.generate(bot_input_ids, max_length=1000, pad_token_id=tokenizer.eos_token_id)
    response_text = tokenizer.decode(response_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)

    return response_text, history

# Function to fetch top books from Google Books API based on genre
def fetch_books_from_google_books(genre):
    GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"
    MAX_RESULTS_PER_PAGE = 40  # Max results per page from Google Books API
    MAX_TOTAL_RESULTS = 100  # Total number of results desired

    books = []
    total_results_fetched = 0

    try:
        while total_results_fetched < MAX_TOTAL_RESULTS:
            params = {
                "q": f"subject:{genre}",
                "orderBy": "relevance",
                "maxResults": min(MAX_RESULTS_PER_PAGE, MAX_TOTAL_RESULTS - total_results_fetched),
                "startIndex": total_results_fetched
            }

            response = requests.get(GOOGLE_BOOKS_API_URL, params=params)
            response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)

            data = response.json().get("items", [])

            for item in data:
                volume_info = item.get("volumeInfo")
                if volume_info:
                    title = volume_info.get("title", "Unknown Title")
                    authors = volume_info.get("authors", ["Unknown Author"])
                    rating = volume_info.get("averageRating", 0.0)

                    book = Book(title=title, authors=authors, rating=rating)
                    books.append(book)
                    total_results_fetched += 1

            if not data:
                break  # Break out of loop if no more results

    except requests.RequestException as e:
        print(f"Error fetching books: {e}")

    return books

# Function to fetch top books based on genre or overall if no genre specified
def get_top_books(query):
    genre_mapping = {
        "science fiction": "science fiction",
        "historical fiction": "historical fiction",
        "mystery": "mystery",
        "fiction": "fiction",
        "horror": "horror",
        "fantasy": "fantasy",
        "romance": "romance",
        "thriller": "thriller",
        "biography": "biography",
        "self-help": "self-help",
        "self help": "self-help"
    }

    genre = ""
    for key in genre_mapping:
        if key in query:
            genre = genre_mapping[key]
            break

    books = fetch_books_from_google_books(genre)
    return books, genre

def get_top_10_books(books):
    top_books = sorted(books, key=lambda x: x.rating, reverse=True)[:10]
    return top_books

# Function to find a book by keyword in the top books list
def find_book_by_keyword(books, keyword):
    for book in books:
        if keyword.lower() in book.title.lower():
            return book
    return None

# Main interaction loop (for testing purposes)

def chat(user_input):
    global books, top_books

    history = []
    response = ""

    if ("top" in user_input or "good" in user_input or "best" in user_input or
        "rated" in user_input or "popular" in user_input or "100" in user_input) and (
        "book" in user_input or "novel" in user_input) and "10 " not in user_input:

        books, genre = get_top_books(user_input.lower())

        if books:
            if genre == "":
                response = f"Fetched top books right now across all genres."
            else:
                response = f"Fetched top 100 books in {genre}."

            for idx, book in enumerate(books, start=1):
                response += f"\n{idx}. {book.title} by {', '.join(book.authors)} (Rating: {book.rating})"

        else:
            response = "Could not fetch books. Please try again."

    elif ("top" in user_input or "good" in user_input or "best" in user_input or
          "rated" in user_input or "popular" in user_input or "10 " in user_input) and (
          "book" in user_input or "novel" in user_input) and ("10 " in user_input or "ten" in user_input):

        top_books = get_top_10_books(books)
        response = "Top 10 books:\n"
        for idx, book in enumerate(top_books, start=1):
            response += f"\n{idx}. {book.title} by {', '.join(book.authors)} (Rating: {book.rating})"

    elif ("find" in user_input or "specific" in user_input or "/find" in user_input):
        keyword = user_input.split(" ", 1)[1].strip()
        selected_book = find_book_by_keyword(top_books,keyword)

        if selected_book:
            response = f"Selected book: {selected_book.title} by {', '.join(selected_book.authors)} (Rating: {selected_book.rating})"
        else:
            response = f"No book found with keyword '{keyword}' in top 10."

    elif any(exit_phrase in user_input.lower() for exit_phrase in ["exit", "quit", "bye", "thank"]):
        response = "Thank you for your interaction. Have a great day ahead!"

    else:
        response, history = generate_response(user_input, history)
        response = f"Bot: {response}"

    return response

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    user_input = request.json.get('user_input', '')
    response = chat(user_input)
    return jsonify({'response': response})

if __name__ == "__main__":
    app.run(debug=True)
