# LeanChems AI CRM

A modern, AI-powered CRM system built with Next.js, Supabase, and OpenAI.

## Features

- 🔐 Secure authentication with Supabase
- 👥 Customer management with AI-powered insights
- 💬 AI chat assistant with memory
- 📊 Data analysis and reporting
- 📱 Telegram notifications for daily updates and real-time alerts
- 🎨 Modern, responsive UI with Tailwind CSS

## Prerequisites

- Node.js 18+ and npm
- Supabase account and project
- OpenAI API key
- Telegram account (for notifications)

## Environment Variables

Create a `.env.local` file in the root directory with the following variables:

```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_api_key

# Telegram Notifications (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
NOTIFICATION_ENABLED=true
```

## Database Setup

1. Create the following tables in your Supabase database:

### customers
```sql
create table customers (
  id uuid default uuid_generate_v4() primary key,
  customer_id text unique not null,
  display_id text unique not null,
  customer_name text not null,
  input_conversation text[] default '{}',
  output_conversation text[] default '{}',
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);
```

### memories
```sql
create table memories (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references auth.users not null,
  memory text not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);
```

### deals
```sql
create table deals (
  id uuid default uuid_generate_v4() primary key,
  input_log text not null,
  ai_response_log text not null,
  created_by uuid references auth.users not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/leanchems-ai-crm.git
cd leanchems-ai-crm
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Telegram Notifications Setup

To enable Telegram notifications for daily deal summaries and real-time updates:

1. Follow the detailed setup guide in [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md)
2. Test your configuration using the provided test script:
   ```bash
   python test_telegram.py
   ```
3. Enable notifications in the CRM dashboard under "Analysis & Reporting" → "Telegram Notifications"

## Building for Production

```bash
npm run build
npm start
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
