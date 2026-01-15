# SaaS Client - Installation Guide

## Overview

SaaS Client is the client-side app that should be installed on each client ERPNext instance. It connects to the main SaaS Manager app to sync data and enforce user limits.

## Installation

### Step 1: Install the App

```bash
cd /path/to/your/bench
bench get-app sass_client
bench --site [your-client-site] install-app sass_client
bench --site [your-client-site] migrate
```

### Step 2: Configure Site Settings

Add to `site_config.json`:

```json
{
  "saas_manager_url": "https://your-main-saas-manager.com",
  "client_type": "ERP"
}
```

### Step 3: Automatic Registration

The site will automatically register with the main SaaS Manager on first sync. The API key will be generated and should be added to `site_config.json`.

### Step 4: Verify Installation

1. Check Error Log for any sync errors
2. Verify hourly sync is working
3. Test user limit enforcement

## Features

- **Automatic Data Sync**: Syncs data hourly to main app
- **User Limit Enforcement**: Enforces user limits based on subscription package
- **Site Registration**: Automatically registers with main app
- **Subscription Status Check**: Checks subscription status from main app

## What Data is Synced

The app syncs the following data to the main SaaS Manager:

- Total Sales Invoices count
- Total Credit Notes count
- Total Purchase Invoices count
- Total Stock Reconciliations count
- Active Users count
- Total Companies count
- Company name
- Client type
- IP address
- Site URL
- Subscription package info
- Subscription status

## User Limit Enforcement

The app automatically enforces user limits when:
- Creating new users
- Enabling existing users

If the limit is reached, an error will be shown preventing user creation/enabling.

## Troubleshooting

### Site Not Syncing

1. Check `saas_manager_url` in `site_config.json`
2. Verify API key is set
3. Check Error Log for sync errors
4. Ensure main app is accessible

### User Limits Not Working

1. Verify subscription is active in main app
2. Check package has `max_users` set
3. Verify API key is correct
4. Check Error Log for errors

## Security

- Only aggregated statistics are sent
- No sensitive data is transmitted
- API key authentication
- Secure HTTPS communication

## Support

For issues:
- Email: akingbolahan12@gmail.com
- Check Error Log in ERPNext
- Review main app documentation
