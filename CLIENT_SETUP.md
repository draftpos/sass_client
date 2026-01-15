# SaaS Client - Setup Guide

This guide explains how to set up the SaaS Client app on client ERPNext instances.

## Installation Steps

### 1. Install the App

```bash
bench get-app sass_client
bench --site [your-client-site] install-app sass_client
bench --site [your-client-site] migrate
```

### 2. Configure Site Settings

Add the following to your `site_config.json` file:

```json
{
  "saas_manager_url": "https://your-main-saas-manager.com",
  "client_type": "ERP"
}
```

**Note**: The `saas_api_key` will be automatically generated when you register the site.

### 3. Register the Site

The site will automatically register on first sync. Just ensure `saas_manager_url` is configured.

Alternatively, you can register manually:

```python
from sass_client.utils.client_sync import register_client_site

api_key = register_client_site(
    site_name="My Client Site",
    company="My Company Name",
    client_type="ERP"  # Options: ERP, Mobile POS, Desktop POS, Fiscalisation
)

# Add the API key to site_config.json:
# "saas_api_key": "generated-api-key"
```

### 4. Automatic Sync

The app automatically syncs data hourly to the main SaaS Manager. No additional configuration needed.

### 5. User Limit Enforcement

User limits are automatically enforced based on your subscription package. The app will prevent creating or enabling users beyond your package limit.

## Configuration Options

### site_config.json Options

| Option | Required | Description | Default |
|--------|----------|-------------|---------|
| `saas_manager_url` | Yes | URL of main SaaS manager app | - |
| `saas_api_key` | Yes* | API key for authentication | Auto-generated |
| `client_type` | No | Type of client (ERP, Mobile POS, Desktop POS, Fiscalisation) | ERP |
| `subscription_package` | No | Package name from main app | - |
| `subscription_active` | No | Whether subscription is active | false |
| `subscription_start_date` | No | Subscription start date | - |
| `subscription_end_date` | No | Subscription end date | - |

*API key is auto-generated on registration, but you can manually set it if needed.

## Manual Sync

To manually trigger a sync:

```python
from sass_client.utils.client_sync import sync_to_main_app
sync_to_main_app()
```

## Check Subscription Status

```python
from sass_client.utils.client_sync import get_site_data
data = get_site_data()
print(data)
```

## Troubleshooting

### Sync Not Working

1. Check that `saas_manager_url` is correctly configured
2. Verify API key is set in `site_config.json`
3. Check Error Log for sync errors
4. Ensure main app is accessible from client site

### User Limit Not Enforcing

1. Verify hooks are configured (should be automatic)
2. Check subscription status in main app
3. Verify package has `max_users` set
4. Check Error Log for limit check errors

### Registration Failed

1. Ensure main app is accessible
2. Check network connectivity
3. Verify site URL is correct
4. Check Error Log for registration errors

## Security

- The client app only has read access to your ERPNext data
- Only aggregated statistics are sent to the main app
- No sensitive data is transmitted
- API key authentication ensures secure communication

## Support

For issues, check the Error Log in ERPNext or contact: akingbolahan12@gmail.com
