from typing import List
from pathlib import Path
import httpx
import bs4
import pandas as pd

def download_html() -> bs4.BeautifulSoup:
    with httpx.Client() as client:
        r = client.get("https://www.tabc.texas.gov/services/tabc-licenses-permits/tabc-license-permit-types/")
        if r.status_code == httpx.codes.OK:
            page = bs4.BeautifulSoup(r.text, 'html.parser')
    return page

def parse_head(head: str) -> tuple:
    head = head.strip()
    i = head.rfind("(")
    return head[(i+1):-1], head[:(i-1)]

def parse_multi_codes(code: str, name: str) -> zip:
    idx = code.find("if")
    codes = code[:idx].strip().split(" or ")
    names = [
        name, 
        f"{name} ({code[idx:].strip().split(' is a ')[1].title()})"
    ]
    return zip(codes,names)

def parse_cards(cards: List[bs4.element.Tag], group: str) -> List[dict]:
    permit_list = list()
    for card in cards:  
        code, name = parse_head(card.select('div.card-header')[0].text)
        info = card.find('p').text.replace(u'\xa0', ' ')
        if len(code) > 2:
            for code, name in parse_multi_codes(code, name):
                permit_list.append({
                    'code': code,
                    'name': name,
                    'info': info,
                    'group': group
                })
        else:
            permit_list.append({
                    'code': code,
                    'name': name,
                    'info': info,
                    'group': group
            })
    return permit_list

def parse_page(page: bs4.BeautifulSoup) -> List[dict]:
    permit_groups = [div.text for div in page.find("main").select("div.row")[0].find_all("h2")]
    permit_types = page.find("main").select("div.row")[0].select("div.authored-accordion")
    permit_list = list()
    for group, accordion in zip(permit_groups, permit_types):
        permit_list.extend(parse_cards(accordion.select("div.accordion-card"), group))
    return permit_list

def get_tabc_permit_types(local_path: str = '/data/tabc_permit_types.csv') -> pd.DataFrame:
    file_path = Path(local_path)
    if file_path.exists():
        df = pd.read_csv(file_path)
    else:
        df = pd.DataFrame(parse_page(download_html()))
        df.to_csv(file_path, index=False)
    return df
