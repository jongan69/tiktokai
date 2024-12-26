# TikTokAI

An automated system for generating and publishing AI-powered TikTok videos.

## Overview

TikTokAI is a Python-based tool that automates the creation and publication of TikTok videos using AI technologies. The system handles everything from content generation to video creation and music addition.

## Features

- AI-powered content generation using GPT
- Automatic video creation and editing
- Music addition and audio processing
- TikTok upload automation
- Image and video search capabilities

## Prerequisites

- Python 3.8+
- FFmpeg
- TikTok account

## Installation

1. Clone the repository:
```
git clone https://github.com/jongan69/tiktokai.git
cd tiktokai
```

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Fill in your credentials and API keys

## Configuration

To login to TikTok, run the following command:
```
python3 login.py
```

## Project Structure
```
tiktokai/
├── videogen/
│   ├── video.py      # Video generation logic
│   ├── gpt.py        # GPT integration
│   ├── search.py     # Image/video search
│   └── addMusic.py   # Music processing
├── login.py          # TikTok authentication
└── lock_facts_bot.py # Main bot logic
```

## Usage

1. Run the bot:
```bash
python lock_facts_bot.py
```

## Features in Detail

### Content Generation
The system uses GPT to generate engaging and relevant content for TikTok videos.

### Video Creation
- Automated video assembly
- Image and video search integration
- Custom transitions and effects
- Music addition and synchronization

### Upload Automation
Handles TikTok login and video upload process automatically.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This project is for educational purposes only. Make sure to comply with TikTok's terms of service and API usage guidelines.

## Support

For support, please open an issue in the GitHub repository.