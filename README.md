Freelance Project Price Predictor
Demo Video
GitHub
________________________________________
Overview
The Freelance Project Price Predictor is an AI-powered system that estimates the price of freelance projects (either fixed-price or hourly) based on project details and client profile.
Instead of relying on guesswork, the model predicts a realistic price range (min → max) by analyzing:
•	Project description, title, and required skills
•	Client country (market influence)
•	Rate type (fixed vs hourly)
This helps freelancers quote more accurately and clients budget more realistically, aligning expectations before bidding.
The system was built using Sentence Transformer embeddings for text, a trainable embedding layer for countries, and a multi-input deep learning model deployed as a Flask web app with a Tailwind CSS frontend.
________________________________________
Dataset Used
•	Freelance project postings dataset (~9k rows)
•	Features:
o	job_title
o	job_description
o	tags_clean (skills/tech stack)
o	client_country
o	rate_type (fixed/hourly)
o	min_price_usd, max_price_usd (targets)
________________________________________
Features
Project Data Ingestion & Preprocessing
•	Combined title + description + tags_clean for semantic representation.
•	Generated 768-dim text embeddings using Sentence Transformers (all-mpnet-base-v2).
•	Encoded client countries using a LabelEncoder + trainable embedding layer.
•	Encoded rate type (fixed, hourly) as binary inputs.
•	Applied log transformation on target prices to stabilize training, inverse-transformed during inference.
Deep Learning Model
•	Multi-input Feedforward Neural Network:
o	Input 1: Text embeddings (768-dim)
o	Input 2: Country embedding (trainable)
o	Input 3: Rate type (binary)
•	Concatenated inputs → Dense layers → Output: [min_price, max_price]
•	Loss: Huber Loss (robust to outliers)
•	Metrics: MAE, MAPE
Flask Web Application
•	Input: Job title, description, skills, rate type, country (dropdown populated from encoder).
•	Output: Predicted price range (min–max).
•	Frontend: Tailwind CSS, clean responsive design.
________________________________________
System Architecture
User (Freelancer / Client) →
Flask Web App (Frontend: Tailwind, HTML/CSS) →
Sentence Transformer (text embeddings) →
Country Encoder + Embedding Layer →
Deep Learning Model (TensorFlow/Keras) →
Inverse Log Transform →
Predicted Price Range →
Flask → Frontend
________________________________________
Tech Stack
Backend: Flask, Python
ML / DL: TensorFlow/Keras, Sentence Transformers, Scikit-learn, NumPy, Pandas
Frontend: HTML, Tailwind CSS (modern UI for input form + results)
Data: Freelance projects dataset (~9k rows)
Deployment: Flask server (local, extendable to cloud platforms like AWS/GCP)
________________________________________
Project Structure
freelance-price-predictor/
│── app.ipynb               # Training pipeline & experiments  
│── backendcode.py          # Flask backend  
│── templates/  
│    └── index.html         # Tailwind frontend (form + results UI)  
│── country_encoder.joblib  # Saved encoder for countries  
│── fixed_price_model.keras # Final trained model (fixed price)  
│── hourly_rate_model.keras # Final trained model (hourly rate)  
│── requirements.txt        # Dependencies  
________________________________________
Challenges & Learnings
Outliers in Prices
•	Problem: Extreme high-priced projects distorted model training.
•	Solution: Used log transform on targets + robust loss (Huber) instead of dropping them, ensuring better handling of high-value projects.
Bias in Dataset
•	Problem: Most jobs were low-cost ($5–50), so model underpredicted high-value jobs.
•	Solution: Balanced dataset by retaining outliers, applied sample weighting and tested stratified approaches.
Input Shape Mismatch
•	Problem: Sentence Transformer initially used (384-d) embeddings clashed with training model (768-d).
•	Solution: Ensured consistent embedding model (all-mpnet-base-v2, 768-dim) at both training and inference.
Frontend Integration
•	Problem: Country dropdown was empty in UI.
•	Solution: Added /get_countries API in Flask to dynamically populate frontend dropdown.
Inverse Transform Missing
•	Problem: Predictions were tiny ($3/hr for AI chatbot).
•	Solution: Added correct inverse log transform (exp) in backend. Predictions corrected (e.g., $15–18/hr).
________________________________________
Author
Akash Gupta
M.Tech Artificial Intelligence, IIT Kharagpur

