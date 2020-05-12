import itertools
import unicodedata

from matplotlib import pyplot as plt


def draw_me():
    fix, axes = plt.subplots(1, 1, figsize=(11, 16), dpi=100)

    words = [
        "spasm reinspecting",
        "paled dormant",
        "surely corinthian",
        "peril samovar",
        "pewits shrew",
        "weeful glueball",
        "excite eyebrows",
        "flew fifteen",
        "quiet thawing",
        "acid chicken",
        "ambo rewiring",
        "survey frogs",
        "lied borrows",
        "if blooddonation",
        "codes jewels",
        "voodoo boodle"
    ]

    mapper = [1, 5, 4, 5, 4, 3, 2, 2, 3, 4, 4, 2, 3, 1, 5, 1, 3, 4, 1, 2, 2, 5, 3, 3, 3]

    colors = ["FFFFFF",  "FAC6A0", "BDABC7", "3b79c0", "4e3d6a"]

    words = [word.replace(" ","")[:11] for word in words]

    # Origin is at the top left.   Positive x to the right.   Positive y is down.
    axes.axis([-2, 16, 16, -2])
    axes.axis('equal')
    axes.axis('off')
    plt.margins(x=0.0, y=0.0, tight=True)

    for row, word in enumerate(words):
        for column, letter in enumerate(word):
            index = mapper[ord(letter) - ord('a')]
            color = colors[index - 1]
            rectangle = plt.Rectangle((column, row), 1, 1, linewidth=2,
                                      color='#' + color)
            axes.add_artist(rectangle)


    plt.show()

def open_me():
    from urllib.request import urlopen
    with open("/tmp/foo", "w") as file:
        for i in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            print(i)
            url = f'https://en.wikipedia.org/wiki/List_of_painters_by_name_beginning_with_"{i}"'
            for line in urlopen(url).readlines():
                temp = line.decode("utf-8")
                if temp.startswith("<li>"):
                    file.write(remove_accents(temp))


def remove_accents(text):
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    text = text.decode("utf-8")
    return str(text)

info = None


def search_me(letters):
    global info
    if info is None:
        with open("/tmp/foo", "r") as file:
            info = file.read()

    for pick in itertools.permutations(letters, 6):
        search = ''.join(pick)
        search = search[0].upper() + search[1:]
        index = 0
        try:
            while True:
                index = info.index(search, index + 1)
                temp1 = info.rfind("\n", 0, index)
                temp2 = info.find("\n", index)
                print(letters, search, info[temp1 + 1: temp2])
        except ValueError:
            pass


def do_search(search: str, file: str):
    index = 0
    try:
        while True:
            index = file.index(search, index + 1)
            temp1 = file.rfind("\n", 0, index)
            temp2 = file.find("\n", index)
            print(search, file[temp1 + 1: temp2])
            index = temp2 + 1
    except ValueError:
        pass




if __name__ == '__main__':
    search_me("cachemojosa")
    search_me("adocliquier")
    search_me("neneelastic")
    search_me("tutackntech")
    search_me("exeststirhi")
    search_me("rustrehnrem")
    search_me("bpsionetage")
    search_me("urespumiced")
    search_me("roralsememe")
    search_me("ytapasdedda")
    search_me("getatibehan")
    search_me("aciniserows")
    search_me("ltownsadunc")
    search_me("linageuuser")
    search_me("ovidincede")
    search_me("pekefretsaw")


