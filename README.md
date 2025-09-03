# AGS AI Assistant 🌴

An intelligent agricultural analysis platform powered by AI, designed to help farmers and agricultural professionals make data-driven decisions.

## Features

- **Document Analysis**: Upload and analyze agricultural documents using OCR and AI
- **Step-by-Step Analysis**: Comprehensive 6-step analysis process
- **Solution Recommendations**: AI-powered recommendations for agricultural challenges
- **Data Visualization**: Interactive charts and graphs for better insights
- **User Management**: Secure authentication and admin panel
- **History Tracking**: Keep track of all your analyses

## Technology Stack

- **Frontend**: Streamlit
- **Backend**: Firebase (Authentication & Database)
- **AI**: Google Gemini AI
- **OCR**: Tesseract
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly, Matplotlib

## Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables (copy `.streamlit/secrets.toml.template` to `.streamlit/secrets.toml`)
4. Run the application:
   ```bash
   streamlit run app.py
   ```

## Deployment

This application is designed to be deployed on Streamlit Cloud. See the deployment section below for detailed instructions.

## Configuration

The application requires several environment variables to be configured:

- Firebase configuration
- Google AI API key
- Admin codes for user management

## License

This project is proprietary software.
