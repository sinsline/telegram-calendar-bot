# Railway Cloud Deployment Documentation

## Deployment Steps

1. **Connect GitHub Repository**
   - Go to https://railway.app
   - Sign in with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select `sinsline/telegram-calendar-bot`

2. **Environment Variables** 
   Set these in Railway Dashboard → Variables:
   
   ```
   TELEGRAM_BOT_TOKEN=<your_bot_token_from_@BotFather>
   
   # Database (from Fastpanel server)
   DATABASE_URL=mysql://lendar_smart:M%3BeXj%400Z%3Aql%3BO%24N%3D@68.183.222.192:3306/lendar_smart
   
   # Calendar settings
   CALENDAR_TIMEZONE=Europe/Berlin
   LOG_LEVEL=INFO
   ENVIRONMENT=production
   
   # Bot behavior
   RATE_LIMIT_PER_MINUTE=20
   RATE_LIMIT_PER_HOUR=200
   RATE_LIMIT_PER_DAY=1000
   
   # NLP settings
   NLP_SUPPORTED_LANGUAGES=ru,de,en
   NLP_CONFIDENCE_THRESHOLD=0.7
   NLP_DEFAULT_EVENT_DURATION=60
   
   # OCR settings
   OCR_LANGUAGES=rus+eng+deu
   OCR_DPI=300
   OCR_IMAGE_MAX_SIZE=4096
   OCR_MAX_FILE_SIZE=10485760
   
   # Speech settings
   SPEECH_MODEL=base
   SPEECH_MAX_FILE_SIZE=26214400
   SPEECH_TIMEOUT=60
   
   # Paths
   PYTHONPATH=/app
   PYTHONUNBUFFERED=1
   DATA_DIR=./data
   LOGS_DIR=./logs
   
   # Security
   SECRET_KEY=railway-production-key-2024
   DEBUG_MODE=False
   
   # Monitoring
   ENABLE_HEALTH_CHECK=True
   HEALTH_CHECK_PORT=8081
   ```

3. **Webhook Configuration**
   After deployment, set webhook URL to connect with Fastpanel web interface:
   ```
   https://<railway-app-url>/webhook
   ```

4. **Monitoring**
   - Railway provides metrics dashboard
   - Logs available in Railway Dashboard
   - Health check endpoint: `https://<app-url>/health`

## Architecture

```
[Telegram] ↔ [Railway Python Bot] ↔ [Fastpanel MySQL DB]
                     ↕
         [Fastpanel Web Interface - lendar.smart-widget.net]
```

## Post-Deployment Tasks

1. **Test Bot Functionality**
   - Send `/start` to bot in Telegram
   - Test voice message recognition
   - Test image OCR
   - Test calendar integration

2. **Configure Google Calendar** (if needed)
   - Create Google Cloud project
   - Enable Calendar API
   - Download credentials.json
   - Upload to Railway or set as environment variable

3. **Monitor Performance**
   - Check Railway metrics
   - Monitor database connections
   - Verify error rates

## Troubleshooting

### Common Issues
- **ImportError**: Check Dockerfile has all system dependencies
- **Database Connection**: Verify DATABASE_URL format and network access
- **Telegram API**: Ensure bot token is correct and bot is started with @BotFather
- **Memory Issues**: Railway free tier has 512MB limit, upgrade if needed

### Log Access
```bash
# Through Railway CLI (optional)
railway login
railway logs --follow
```

## Costs

- **Railway Free Tier**: $5 credit/month, then $0.000463/GB-hour
- **Estimated Monthly Cost**: ~$3-8/month for small-medium usage
- **Database**: Included via Fastpanel server

## Next Steps

1. Deploy to Railway
2. Test all functionality  
3. Connect webhook to Fastpanel web interface
4. Set up monitoring and alerts
5. Document user guide for Sergey