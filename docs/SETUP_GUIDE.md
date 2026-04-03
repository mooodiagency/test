# Meta Integration Setup Guide

## Stap 1: Meta Developer Account

1. Ga naar **https://developers.facebook.com**
2. Log in met je Facebook account
3. Accepteer de developer voorwaarden

## Stap 2: Meta App Aanmaken

1. Klik op **"Create App"** (rechtsboven)
2. Kies **"Other"** als use case → klik Next
3. Kies **"Business"** als app type → klik Next
4. Vul in:
   - **App name**: bijv. "Claude Social Manager"
   - **Contact email**: jouw email
   - **Business Account**: selecteer of maak een nieuwe
5. Klik **"Create App"**

## Stap 3: API Permissions Instellen

In je app dashboard:

1. Ga naar **App Settings > Basic**
   - Noteer je **App ID** en **App Secret**

2. Ga naar **Add Products** en voeg toe:
   - **Facebook Login for Business**
   - **Instagram Graph API**

3. Ga naar **Tools > Graph API Explorer**
   - Selecteer je app
   - Klik **"Generate Access Token"**
   - Selecteer deze permissions:
     - `pages_manage_posts`
     - `pages_read_engagement`
     - `pages_show_list`
     - `pages_read_user_content`
     - `instagram_basic`
     - `instagram_content_publish`
     - `instagram_manage_insights`
     - `read_insights`

## Stap 4: Page Access Token

1. In Graph API Explorer, selecteer je **Facebook Page**
2. Kopieer het **Page Access Token**
3. Om een long-lived token te krijgen:
   ```
   GET /oauth/access_token?grant_type=fb_exchange_token
       &client_id={APP_ID}
       &client_secret={APP_SECRET}
       &fb_exchange_token={SHORT_LIVED_TOKEN}
   ```

## Stap 5: Instagram Business Account ID

1. In Graph API Explorer:
   ```
   GET /{page-id}?fields=instagram_business_account
   ```
2. Noteer het **instagram_business_account.id**

## Stap 6: .env Configureren

Kopieer `.env.example` naar `.env` en vul je credentials in:

```bash
cp .env.example .env
```

Vul in:
- `META_APP_ID` = je App ID
- `META_APP_SECRET` = je App Secret
- `META_ACCESS_TOKEN` = je Page Access Token
- `META_PAGE_ID` = je Facebook Page ID
- `INSTAGRAM_BUSINESS_ACCOUNT_ID` = je IG Business Account ID

## Stap 7: MCP Server Configureren

Voeg dit toe aan je Claude Code MCP settings:

```json
{
  "mcpServers": {
    "meta-integration": {
      "command": "python",
      "args": ["-m", "meta_integration.mcp_server.server"],
      "cwd": "/pad/naar/dit/project"
    }
  }
}
```

## Stap 8: Testen

```bash
python -m meta_integration.test_connection
```

Dit test of je tokens geldig zijn en of je de juiste permissions hebt.
