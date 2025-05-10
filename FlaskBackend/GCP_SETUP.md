# Setting up Google Cloud Text-to-Speech

This application uses Google Cloud Text-to-Speech for generating speech from text. Follow these steps to set up the service:

## Prerequisites

1. A Google Cloud account
2. A Google Cloud project with billing enabled
3. The Text-to-Speech API enabled

## Setup Steps

1. Create or select a Google Cloud project:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. Enable the Text-to-Speech API:
   - Go to [APIs & Services > Library](https://console.cloud.google.com/apis/library)
   - Search for "Text-to-Speech API"
   - Click "Enable"

3. Create a service account:
   - Go to [IAM & Admin > Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
   - Click "Create Service Account"
   - Give it a name and description
   - Add the "Cloud Text-to-Speech User" role
   - Create a JSON key and download it

4. Set up your credentials:
   - Place the downloaded JSON key file in a secure location
   - Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to this file:
     ```
     export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-project-credentials.json"
     ```
   - For development, you can add this to your `.env` file

## Testing

To verify your setup is working correctly:

1. Run the Flask backend
2. Test the basic TTS endpoint with a simple request

## Troubleshooting

If you encounter issues:
1. Verify your credentials file is in the correct location and has the right permissions
2. Check that the Text-to-Speech API is enabled in your project
3. Ensure your service account has the proper permissions
4. Check the application logs for specific error messages from the Google Cloud API
