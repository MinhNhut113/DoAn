from dotenv import load_dotenv
import os, traceback
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def main():
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

        logger.info('Listing models from Google Generative API...')
        models = genai.list_models()
        count = 0
        for m in models:
            count += 1
            try:
                # model may be dict-like
                if isinstance(m, dict):
                    name = m.get('name') or m.get('id') or str(m)
                else:
                    name = getattr(m, 'name', str(m))
                logger.info(f"- {name}")
            except Exception as e:
                logger.debug(f"Failed to extract model name: {e}")
                logger.info(f"- {m}")

        logger.info(f'Total models found: {count}')

    except Exception as e:
        logger.error('Error listing models:')
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    main()
