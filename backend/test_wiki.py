import wikipediaapi

wiki = wikipediaapi.Wikipedia('PoliticalPulse (harshvardhan.khamkar@example.com)', 'en')

page = wiki.page('Bharatiya Janata Party')

if page.exists():
    print(f"Title: {page.title}")
    print(f"Summary: {page.summary[:500]}...")
    
    history_section = None
    for section in page.sections:
        if section.title.lower() == 'history':
            history_section = section
            break
            
    if history_section:
        print(f"History (Start): {history_section.text[:500]}...")
    else:
        print("History section not found directly, checking sub-sections...")
        # Sometimes History is a parent section with subsections
        for section in page.sections:
             if 'history' in section.title.lower():
                 print(f"Found something like history: {section.title}")
                 print(f"Text: {section.text[:200]}...")
else:
    print("Page not found")
