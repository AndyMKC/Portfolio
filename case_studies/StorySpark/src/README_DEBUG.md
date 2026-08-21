# Debugging Guide

## Prerequisites

### 1. Install Google Cloud SDK
If you haven't already installed the Google Cloud SDK, download it from:
https://cloud.google.com/sdk/docs/install

### 2. Authenticate with Google Cloud
Before debugging, you need to authenticate with Google Cloud to get an ID token for API authorization.

```bash
# Login with your Google account
gcloud auth login
```

This will open a browser window where you can:
- Select your Google account (e.g., `andy.ming.kong.cheng@gmail.com`)
- Review the permissions and click "Allow"

### 3. Generate Application Default Credentials
For BigQuery access within the Docker container:

```bash
# Generate application default credentials
gcloud auth application-default login
```

This creates the credentials file at:
- **Windows**: `C:\Users\[username]\AppData\Roaming\gcloud\application_default_credentials.json`
- **Linux/Mac**: `~/.config/gcloud/application_default_credentials.json`

## Starting the Debug Session

1. **Build and start the container**:
   ```bash
   cd src
   make dev
   ```

2. **Attach the debugger** in VS Code:
   - Open the Run and Debug panel (Ctrl+Shift+D or Cmd+Shift+D)
   - Select "Debug StorySpark Server"
   - Press F5

3. **Wait for the debugger to attach**:
   - The container will pause until VS Code connects
   - Once attached, the server will start serving requests

## Getting a Bearer Token for Swagger

### Method 1: Using gcloud (Recommended)

After attaching the debugger and the server is running:

```bash
# Get your ID token for API authorization
gcloud auth print-identity-token
```

This outputs a token like:
```
ya29.a0AfH6SMBx...
```

### Method 2: Using a Specific Account

If you have multiple authenticated Google accounts, you can:

```bash
# List all available accounts
gcloud auth list

# Set the active account (if needed)
gcloud config set account YOUR_EMAIL@example.com

# Then get the ID token
gcloud auth print-identity-token
```

## Authorizing in Swagger UI

1. Open Swagger UI: http://localhost:8000/docs

2. Click the 🔒 **"Authorize"** button in the top-right corner

3. In the authorization dialog:
   - For the **Bearer** field, enter your token with the format:
     ```
     Bearer ya29.a0AfH6SMBx...
   ```
   (Don't forget to include the word "Bearer" followed by a space before the token)

4. Click **"Authorize"** then **"Close"**

5. You should now see the lock icons change and API endpoints become accessible

## Testing API Endpoints

Once authenticated in Swagger, you can test:
- **GET /books** - Retrieve all books
- **POST /books** - Add a new book
- **GET /recommendation** - Get book recommendations
- etc.

## Token Expiration

ID tokens expire in approximately **1 hour**. You will need to:
1. Get a new token: `gcloud auth print-identity-token`
2. Re-authorize in Swagger with the new token

## Troubleshooting

### "No active device" error with gcloud auth application-default login
If you're in a headless environment, use:
```bash
gcloud auth application-default login --no-user-output-enabled
```

### "Permission denied" or authentication errors in BigQuery
Make sure you have the correct permissions on your Google Cloud project and that your account is in the `ALLOWED_USERS` list in `app/auth.py`.

### Server doesn't start after debugger attaches
Check that port 8000 on your host is not already in use:
```bash
docker ps
```

### Docker port mapping issues
Ensure these ports are available:
- 8000 (HTTP API)
- 5678 (Debugpy)

### Credentials file not found in container
Verify your credentials file exists:
```bash
# On Windows:
ls "C:\Users\[your-username]\AppData\Roaming\gcloud\application_default_credentials.json"

# On Mac/Linux:
ls ~/.config/gcloud/application_default_credentials.json

Then restart the container:
make dev
```

## Development vs Production Notes

- In **dev mode**, you can use mock data - simply call `/books` without a bearer token and the API will return mock book data
- In **production**, all protected endpoints require a valid Google ID token
- The allowed users list is defined in `src/app/auth.py`:
  ```python
  ALLOWED_USERS = [
      "andy.ming.kong.cheng@gmail.com",
      "codingdolly@gmail.com",
  ]
  ```