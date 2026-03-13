"""
Full Indian Political Party Seed Script
Populates parties + leaders with real 2024 Lok Sabha data.
Run from the backend/ directory:  python seed_parties.py
"""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.parties import Party, PartyLeader

# ---------------------------------------------------------------------------
# Party data — 2024 Lok Sabha election results + wiki-style info
# ---------------------------------------------------------------------------

PARTIES = [
    {
        "name": "Bharatiya Janata Party",
        "short_name": "BJP",
        "ideology": "Right-wing, Hindutva, Economic Nationalism, Social Conservatism",
        "founded_year": 1980,
        "color_hex": "#FF9933",
        "website": "https://www.bjp.org/",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Bharatiya_Janata_Party_logo.svg/200px-Bharatiya_Janata_Party_logo.svg.png",
        "states_won": 12,
        "total_mps": 240,
        "total_mlas": 1411,
        "vote_share_percentage": "36.56",
        "overview": (
            "The Bharatiya Janata Party (BJP) is India's largest political party by membership and one of the largest "
            "globally. Founded in 1980 as a successor to the Bharatiya Lok Dal, it espouses Hindu nationalism (Hindutva) "
            "combined with economic liberalism. Since 2014 the BJP has formed the central government under Prime Minister "
            "Narendra Modi and leads the National Democratic Alliance (NDA). The party's grassroots strength is built "
            "through its ideological parent organisation, the Rashtriya Swayamsevak Sangh (RSS)."
        ),
        "history": (
            "The BJP emerged from the Janata Party after the Emergency era (1975–77). Leaders like Atal Bihari Vajpayee "
            "and L.K. Advani shaped its early ideology. The 1984 elections returned just 2 Lok Sabha seats, but the Ram "
            "Janmabhoomi movement of the late 1980s and 1990s revived the party sharply. Vajpayee led two BJP-headed "
            "coalition governments (1998–2004). Following a decade in opposition, Narendra Modi led the party to an "
            "outright majority in 2014 — the first for any party since 1984 — and retained power in 2019. In 2024 the "
            "BJP won 240 seats, remaining the single largest party and continuing in government as part of the NDA."
        ),
        "policies": (
            "Key policies include 'Make in India' industrial drive, GST implementation, Ayushman Bharat health insurance, "
            "PM Awas Yojana (housing for all), abrogation of Article 370 in Jammu & Kashmir, Uniform Civil Code debate, "
            "infrastructure-led development (roads, railways, airports), and digital India initiatives. Internationally "
            "the BJP promotes a strong sovereign foreign policy, emphasising strategic autonomy."
        ),
        "leaders": [
            {"name": "Narendra Modi",    "position": "Prime Minister / Parliamentary Leader", "twitter_handle": "narendramodi",  "display_order": 1},
            {"name": "Amit Shah",        "position": "Home Minister / National President",     "twitter_handle": "AmitShah",       "display_order": 2},
            {"name": "J.P. Nadda",       "position": "BJP National President",                 "twitter_handle": "JPNadda",        "display_order": 3},
            {"name": "Rajnath Singh",     "position": "Defence Minister",                      "twitter_handle": "rajnathsingh",   "display_order": 4},
        ],
    },
    {
        "name": "Indian National Congress",
        "short_name": "INC",
        "ideology": "Centrism, Social Liberalism, Secularism, Social Democracy",
        "founded_year": 1885,
        "color_hex": "#19AAED",
        "website": "https://inc.in/",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6c/Indian_National_Congress_hand_logo.svg/200px-Indian_National_Congress_hand_logo.svg.png",
        "states_won": 3,
        "total_mps": 99,
        "total_mlas": 710,
        "vote_share_percentage": "21.19",
        "overview": (
            "The Indian National Congress (INC), commonly called the Congress party, is the oldest and one of the "
            "most historically significant political parties in India. Founded in 1885, it spearheaded the Indian "
            "independence movement and governed India for much of the post-independence era. It currently leads the "
            "Indian National Developmental Inclusive Alliance (INDIA) opposition bloc."
        ),
        "history": (
            "Congress was the primary vehicle of the Indian independence movement under Mahatma Gandhi, Jawaharlal Nehru, "
            "and Subhas Chandra Bose. After independence, Nehru served as PM for 17 years, followed by Indira Gandhi "
            "(who split the party in 1969). Rajiv Gandhi succeeded her after her assassination in 1984. The party governed "
            "under Manmohan Singh from 2004–2014 as part of the UPA coalition. In 2024, Congress won 99 Lok Sabha seats "
            "— its best performance since 2009 — under the leadership of Rahul Gandhi."
        ),
        "policies": (
            "Congress platforms include Minimum Income Guarantee (NYAY), MGNREGA expansion, Right to Education, Aadhaar "
            "welfare linkage, farm loan waivers, secularism, reservation protections, and a mixed-economy approach. The "
            "2024 'Five Guarantees' manifesto promised legal MSP, caste census, wealth redistribution, and strengthening "
            "of MGNREGA."
        ),
        "leaders": [
            {"name": "Mallikarjun Kharge", "position": "National President",             "twitter_handle": "kharge",         "display_order": 1},
            {"name": "Rahul Gandhi",        "position": "Leader of Opposition, Lok Sabha", "twitter_handle": "RahulGandhi",    "display_order": 2},
            {"name": "Priyanka Gandhi Vadra","position": "General Secretary",              "twitter_handle": "priyankagandhi", "display_order": 3},
            {"name": "Shashi Tharoor",      "position": "MP, Thiruvananthapuram",          "twitter_handle": "ShashiTharoor",  "display_order": 4},
        ],
    },
    {
        "name": "Samajwadi Party",
        "short_name": "SP",
        "ideology": "Social Democracy, Socialism, Secularism, OBC Politics",
        "founded_year": 1992,
        "color_hex": "#E31837",
        "website": "https://samajwadiparty.in/",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Samajwadi_Party_logo.svg/200px-Samajwadi_Party_logo.svg.png",
        "states_won": 0,
        "total_mps": 37,
        "total_mlas": 111,
        "vote_share_percentage": "6.97",
        "overview": (
            "The Samajwadi Party (SP) is a major political force in Uttar Pradesh and a key component of the INDIA "
            "alliance. It draws its support primarily from OBC communities, particularly Yadavs, and Muslims. Founded "
            "by Mulayam Singh Yadav, the party is currently led by his son Akhilesh Yadav, who served as Chief Minister "
            "of Uttar Pradesh from 2012–2017."
        ),
        "history": (
            "SP was founded in 1992 by Mulayam Singh Yadav after breaking away from the Janata Dal. It came to power "
            "in UP in 1993, 2003, and 2012. Akhilesh Yadav succeeded his father as party president in 2017 after an "
            "internal power struggle. In the 2024 Lok Sabha elections, SP had a strong showing, winning 37 seats — "
            "its best ever national tally — riding on anti-incumbency against the BJP in Uttar Pradesh."
        ),
        "policies": (
            "SP focuses on social justice, OBC and minority welfare, farmers' rights, public sector employment, and "
            "secularism. The party advocates for caste-based census, strengthening MGNREGA, and reversing privatisation "
            "of public sector units."
        ),
        "leaders": [
            {"name": "Akhilesh Yadav", "position": "National President / Former CM UP", "twitter_handle": "yadavakhilesh", "display_order": 1},
            {"name": "Dimple Yadav",    "position": "MP, Mainpuri",                     "twitter_handle": "dimpleyadav",   "display_order": 2},
        ],
    },
    {
        "name": "All India Trinamool Congress",
        "short_name": "AITC",
        "ideology": "Centrism, Populism, Bengali Regionalism, Social Liberalism",
        "founded_year": 1998,
        "color_hex": "#00A550",
        "website": "https://www.aitcofficial.org/",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/AITC_Logo.svg/200px-AITC_Logo.svg.png",
        "states_won": 1,
        "total_mps": 29,
        "total_mlas": 215,
        "vote_share_percentage": "3.92",
        "overview": (
            "The All India Trinamool Congress (AITC or TMC) is the ruling party of West Bengal under Chief Minister "
            "Mamata Banerjee. Founded in 1998 after Mamata broke from the Congress party, it became the dominant force "
            "in West Bengal politics after defeating the Left Front in 2011, ending their 34-year rule."
        ),
        "history": (
            "AITC was formed by Mamata Banerjee in 1998 as a regional alternative to Congress in West Bengal. It won "
            "state power in 2011 and has retained it through 2016 and 2021 elections, defeating the BJP's aggressive "
            "campaign in 2021. In the 2024 Lok Sabha elections, TMC won 29 seats in West Bengal against a strong BJP challenge."
        ),
        "policies": (
            "TMC's flagship programmes in West Bengal include Kanyashree (girl-child welfare), Lakshmir Bhandar (cash "
            "transfer to women), Swasthya Sathi (health insurance), Rupashri (marriage assistance), and various food "
            "security schemes. Nationally, the party advocates for stronger state rights (federalism), social welfare "
            "schemes, and protection of minority rights."
        ),
        "leaders": [
            {"name": "Mamata Banerjee", "position": "Chief Minister of West Bengal / Party Supremo", "twitter_handle": "MamataOfficial", "display_order": 1},
            {"name": "Abhishek Banerjee","position": "National General Secretary",                   "twitter_handle": "abhishekaitc",   "display_order": 2},
        ],
    },
    {
        "name": "Dravida Munnetra Kazhagam",
        "short_name": "DMK",
        "ideology": "Dravidian Politics, Social Democracy, Secularism, Federalism",
        "founded_year": 1949,
        "color_hex": "#CC0000",
        "website": "https://www.dmk.in/",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/DMK_Party_Flag.svg/200px-DMK_Party_Flag.svg.png",
        "states_won": 1,
        "total_mps": 22,
        "total_mlas": 133,
        "vote_share_percentage": "2.22",
        "overview": (
            "The Dravida Munnetra Kazhagam (DMK) is the ruling party of Tamil Nadu, founded by C.N. Annadurai in 1949 "
            "as a splinter of the Dravidar Kazhagam. It is currently led by M.K. Stalin, who also serves as Chief "
            "Minister of Tamil Nadu. The party is rooted in Dravidian ideology and social justice politics."
        ),
        "history": (
            "DMK broke away from the Dravidar Kazhagam in 1949 advocating linguistic nationalism and Dravidian pride. "
            "It came to power in Tamil Nadu in 1967 ending the Congress dominance. The party has alternated with AIADMK "
            "in governing the state. M. Karunanidhi led the party for over 50 years until his death in 2018, after which "
            "M.K. Stalin took charge. DMK returned to power in Tamil Nadu in 2021 and performed strongly in 2024 "
            "Lok Sabha elections, sweeping 22 of 39 seats."
        ),
        "policies": (
            "DMK advocates for Dravidian federalism, Tamil cultural rights, social justice (reservation expansion), "
            "welfare state, NEET exam abolition, and strong fiscal autonomy for states. Its welfare programmes include "
            "free rice, subsidised electricity, Kalaignar Magalir Urimai (women's cash transfer), and breakfast schemes "
            "for school children."
        ),
        "leaders": [
            {"name": "M.K. Stalin",    "position": "Chief Minister of Tamil Nadu / Party President", "twitter_handle": "mkstalin",    "display_order": 1},
            {"name": "Udhayanidhi Stalin","position": "Deputy CM / Treasurer",                       "twitter_handle": "Udhaystalin", "display_order": 2},
            {"name": "T.R. Baalu",      "position": "Lok Sabha MP / Senior Leader",                  "twitter_handle": None,          "display_order": 3},
        ],
    },
    {
        "name": "Aam Aadmi Party",
        "short_name": "AAP",
        "ideology": "Populism, Anti-corruption, Social Liberalism, Good Governance",
        "founded_year": 2012,
        "color_hex": "#0066CC",
        "website": "https://aamaadmiparty.org/",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Aam_Aadmi_Party_logo.svg/200px-Aam_Aadmi_Party_logo.svg.png",
        "states_won": 1,
        "total_mps": 3,
        "total_mlas": 62,
        "vote_share_percentage": "1.09",
        "overview": (
            "The Aam Aadmi Party (AAP) was born out of the 2011 India Against Corruption movement led by social activist "
            "Anna Hazare. It stunned politics with an unprecedented 67/70 seat sweep in the Delhi 2015 assembly elections "
            "and currently governs Delhi and previously Punjab. Led by Arvind Kejriwal, AAP positions itself as an "
            "alternative to traditional parties on governance and transparency."
        ),
        "history": (
            "AAP was formally founded in November 2012. It contested Delhi elections in December 2013 and formed a "
            "short-lived minority government with Congress support. After resigning in 49 days, it went on to win 67 "
            "of 70 seats in 2015 — one of the largest assembly majorities in Indian history. AAP retained Delhi in 2020 "
            "and expanded to Punjab in 2022, defeating all established parties there. In 2024 Lok Sabha elections, "
            "its performance was moderated due to leadership controversies."
        ),
        "policies": (
            "AAP's governance model in Delhi includes free electricity (up to 200 units), free water, free bus travel "
            "for women, Mohalla Clinics (free primary healthcare), Delhi government school transformation, and "
            "the Kejriwal government's e-governance initiatives. In Punjab, similar welfare schemes have been launched "
            "alongside anti-drug campaigns."
        ),
        "leaders": [
            {"name": "Arvind Kejriwal", "position": "National Convener / Former CM Delhi", "twitter_handle": "ArvindKejriwal", "display_order": 1},
            {"name": "Bhagwant Mann",    "position": "Chief Minister of Punjab",            "twitter_handle": "BhagwantMann",   "display_order": 2},
            {"name": "Raghav Chadha",    "position": "Rajya Sabha MP",                     "twitter_handle": "raghav_chadha",  "display_order": 3},
            {"name": "Atishi",           "position": "Senior Leader / Former Minister",     "twitter_handle": "AtishiAAP",      "display_order": 4},
        ],
    },
    {
        "name": "Bahujan Samaj Party",
        "short_name": "BSP",
        "ideology": "Ambedkarism, Social Justice, Dalit Empowerment, Secularism",
        "founded_year": 1984,
        "color_hex": "#22409A",
        "website": "http://www.bspindia.org/",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Bahujan_Samaj_Party_flag.svg/200px-Bahujan_Samaj_Party_flag.svg.png",
        "states_won": 0,
        "total_mps": 0,
        "total_mlas": 1,
        "vote_share_percentage": "1.82",
        "overview": (
            "The Bahujan Samaj Party (BSP) was founded by Kanshi Ram in 1984 to represent Dalit, Adivasi, OBC, and "
            "religious minority communities — collectively called Bahujan ('majority people'). Led for decades by "
            "Mayawati, it has governed Uttar Pradesh four times with Mayawati as Chief Minister. The party's philosophy "
            "is rooted in B.R. Ambedkar's social justice thinking."
        ),
        "history": (
            "Kanshi Ram built a cadre-based movement through the DS4 and BAMCEF organisations before founding BSP. "
            "The party's electoral high point was the 2007 UP election under Mayawati where it won an outright majority. "
            "In 2019, BSP won 10 Lok Sabha seats in alliance with SP but went solo in 2024, resulting in zero seats "
            "while polling 9.4 million votes. The 2024 result reflects a significant decline from its earlier strength."
        ),
        "policies": (
            "BSP advocates for strict implementation of SC/ST reservation policies, land redistribution, anti-brahminism, "
            "abolition of caste-based discrimination, strengthening of the SC/ST Prevention of Atrocities Act, and "
            "expanded welfare for marginalised communities. Economically it supports government-led development with "
            "special focus on rural and Dalit welfare."
        ),
        "leaders": [
            {"name": "Mayawati",     "position": "National President / Former CM UP", "twitter_handle": None,          "display_order": 1},
            {"name": "Satish Mishra","position": "Rajya Sabha MP / General Secretary", "twitter_handle": None,          "display_order": 2},
        ],
    },
    {
        "name": "Communist Party of India (Marxist)",
        "short_name": "CPI(M)",
        "ideology": "Marxism–Leninism, Communism, Secularism, Left-wing Federalism",
        "founded_year": 1964,
        "color_hex": "#CC0000",
        "website": "https://cpim.org/",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Hammer_and_sickle.svg/200px-Hammer_and_sickle.svg.png",
        "states_won": 1,
        "total_mps": 4,
        "total_mlas": 62,
        "vote_share_percentage": "0.89",
        "overview": (
            "The Communist Party of India (Marxist) is the largest party of the Indian left. It split from the "
            "Communist Party of India (CPI) in 1964. It has been a dominant force in West Bengal (ruling from 1977–2011), "
            "Kerala (intermittently), and Tripura. Currently, it leads the Left Democratic Front (LDF) government in "
            "Kerala under Chief Minister Pinarayi Vijayan and is part of the INDIA alliance nationally."
        ),
        "history": (
            "CPI(M) was formed as a result of ideological differences within the Communist Party of India, particularly "
            "around the Sino-Soviet split. It governed West Bengal for 34 consecutive years (1977–2011) under Jyoti Basu "
            "and Buddhadeb Bhattacharya. The party retains significant influence in Kerala and is the focal party of "
            "the Indian left. In 2024 it won 4 Lok Sabha seats, all from Kerala and Tamil Nadu."
        ),
        "policies": (
            "CPI(M) advocates for land reform, public sector expansion, opposition to privatisation, universal health and "
            "education, strong labour rights, anti-imperialism, and comprehensive social security. In Kerala its governance "
            "model ('Kerala model') emphasises high social indicators with relatively low per-capita income."
        ),
        "leaders": [
            {"name": "Sitaram Yechury", "position": "General Secretary (d. 2024)",      "twitter_handle": "SitaramYechury", "display_order": 1},
            {"name": "Pinarayi Vijayan","position": "Chief Minister of Kerala",          "twitter_handle": "vijayanpinarayi", "display_order": 2},
            {"name": "Brinda Karat",    "position": "Politburo Member / Rajya Sabha",   "twitter_handle": "BrindaKarat",    "display_order": 3},
        ],
    },
    {
        "name": "Telugu Desam Party",
        "short_name": "TDP",
        "ideology": "Telugu Regionalism, Centrism, Economic Liberalism",
        "founded_year": 1982,
        "color_hex": "#FFD700",
        "website": "https://www.telugudesam.org/",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/TDP_Party_Symbol.jpg/200px-TDP_Party_Symbol.jpg",
        "states_won": 1,
        "total_mps": 16,
        "total_mlas": 135,
        "vote_share_percentage": "1.59",
        "overview": (
            "The Telugu Desam Party (TDP) is a major regional party representing Andhra Pradesh, founded by legendary "
            "actor and politician N.T. Rama Rao in 1982. Currently led by N. Chandrababu Naidu, TDP is part of the NDA "
            "coalition and returned to power in Andhra Pradesh in 2024 after defeating the YSRCP."
        ),
        "history": (
            "TDP was founded to challenge Congress dominance in Andhra Pradesh. N.T. Rama Rao's charisma brought the "
            "party to power in 1983. Chandrababu Naidu later became its dominant figure after the 1995 internal revolt. "
            "TDP governed AP and the undivided state across multiple terms. After bifurcation in 2014, it governed "
            "Andhra Pradesh under Naidu. It lost to YSRCP in 2019 but staged a strong comeback in 2024, winning 135 "
            "assembly seats and 16 Lok Sabha seats."
        ),
        "policies": (
            "TDP emphasises Telugu pride and development of Andhra Pradesh. Key policies include Amaravati capital city "
            "development, infrastructure investment, welfare programmes like Anna Canteens, and technology-driven "
            "governance (e-governance was pioneered by Naidu in Hyderabad). In 2024, the party promised 'Super Six' "
            "welfare guarantees including cash transfers, free gas cylinders, and employment support."
        ),
        "leaders": [
            {"name": "N. Chandrababu Naidu","position": "Chief Minister of Andhra Pradesh / Party President", "twitter_handle": "ncbn",           "display_order": 1},
            {"name": "Nara Lokesh",          "position": "Cabinet Minister / General Secretary",              "twitter_handle": "naralokesh",      "display_order": 2},
        ],
    },
    {
        "name": "Janata Dal (United)",
        "short_name": "JD(U)",
        "ideology": "Social Democracy, Secularism, Regionalism (Bihar), Federalism",
        "founded_year": 1999,
        "color_hex": "#1D7A32",
        "website": "https://jdu.org.in/",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Janata_Dal_%28United%29_logo.svg/200px-Janata_Dal_%28United%29_logo.svg.png",
        "states_won": 1,
        "total_mps": 12,
        "total_mlas": 43,
        "vote_share_percentage": "1.10",
        "overview": (
            "The Janata Dal (United) [JD(U)] is a major political party in Bihar, led by Chief Minister Nitish Kumar. "
            "It is a key NDA ally and has governed Bihar in coalition with the BJP for most of the period since 2005. "
            "Nitish Kumar is known for the 'Bihar model' of development focused on law and order, roads, and female empowerment."
        ),
        "history": (
            "JD(U) was formed in 1999 out of a merger of various Janata Dal factions. Nitish Kumar became Bihar CM in "
            "2005 and transformed the state's governance. The party has oscillated between alliance with BJP and opposition, "
            "most recently rejoining the NDA in 2024. In the 2024 Lok Sabha elections, JD(U) won 12 seats, providing "
            "crucial support to the NDA majority."
        ),
        "policies": (
            "JD(U) focuses on Bihar-specific development: road construction (Bihar ranks high in rural roads), prohibition "
            "(total ban on alcohol in Bihar), women empowerment (Jeevika SHGs, cycle scheme for girls), and special "
            "category status demand for Bihar. Nitish Kumar's 'sushasan' (good governance) is the party's central narrative."
        ),
        "leaders": [
            {"name": "Nitish Kumar",  "position": "Chief Minister of Bihar / Party President", "twitter_handle": "NitishKumar", "display_order": 1},
            {"name": "Lalan Singh",   "position": "Lok Sabha MP / Senior Leader",              "twitter_handle": None,          "display_order": 2},
        ],
    },
]

# ---------------------------------------------------------------------------
# Seed function
# ---------------------------------------------------------------------------

def seed_parties():
    db: Session = SessionLocal()
    try:
        inserted = 0
        updated  = 0

        for p in PARTIES:
            leaders_data = p.pop("leaders", [])

            # Upsert party
            existing = (
                db.query(Party).filter(Party.short_name == p["short_name"]).first()
                or db.query(Party).filter(Party.name == p["name"]).first()
            )

            if existing:
                print(f"  Updating: {p['name']}")
                for k, v in p.items():
                    setattr(existing, k, v)
                party_obj = existing
                updated += 1
            else:
                print(f"  Inserting: {p['name']}")
                party_obj = Party(**p)
                db.add(party_obj)
                db.flush()          # get party_obj.id
                inserted += 1

            # Replace leaders
            db.query(PartyLeader).filter(PartyLeader.party_id == party_obj.id).delete(
                synchronize_session=False
            )
            for ld in leaders_data:
                db.add(PartyLeader(party_id=party_obj.id, **ld))

        db.commit()
        print(f"\n✅  Done — Inserted: {inserted}  Updated: {updated}")

    except Exception as e:
        db.rollback()
        print(f"\n❌  Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱  Seeding Indian political party data...\n")
    seed_parties()
