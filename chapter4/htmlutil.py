from bs4 import BeautifulSoup


def html_slim(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for i in soup.find_all(True):
        for name in list(i.attrs):
            if i[name] and name not in ["class"]:  # github trending
                del i[name]

    for i in soup.find_all(["svg", "img", "video", "audio"]):
        i.decompose()
    return str(soup)


def html_slim_hf(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for i in soup.find_all(True):
        for name in list(i.attrs):
            if i[name] and name not in ["class", "href", "a"]:  # huggingface paper
                del i[name]

    for i in soup.find_all(["svg", "img", "video", "audio"]):
        i.decompose()
    return str(soup)


if __name__ == "__main__":
    with open("huggingface-papers-raw.html") as fr:
        html = fr.read()
        with open("huggingface-papers-slim.html", "w") as fw:
            fw.write(html_slim_hf(html))
