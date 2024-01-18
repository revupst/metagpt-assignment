from bs4 import BeautifulSoup


def html_slim(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for i in soup.find_all(True):
        for name in list(i.attrs):
            if i[name] and name not in ["class"]:
                del i[name]

    for i in soup.find_all(["svg", "img", "video", "audio"]):
        i.decompose()
    return str(soup)


if __name__ == "__main__":
    with open("github-trending-raw.html") as fr:
        html = fr.read()
        with open("github-trending-slim.html", "w") as fw:
            fw.write(html_slim(html))
