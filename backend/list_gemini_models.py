from dotenv import load_dotenv
import os, traceback

load_dotenv()

def main():
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

        print('Listing models from Google Generative API...')
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
                print(f"- {name}")
            except Exception:
                print('-', m)

        print(f'Total models found: {count}')

    except Exception as e:
        print('Error listing models:')
        traceback.print_exc()

if __name__ == '__main__':
    main()
