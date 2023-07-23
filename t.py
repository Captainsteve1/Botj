class Zee5:
    def __init__(self, mainUrl):
        self.raw = ""
        if "https://" in mainUrl or "http://" in mainUrl:
            mainUrl = mainUrl.split(':', 1)[1]
            print(mainUrl)
            self.raw = mainUrl.split(':', 1)
            if len(self.raw) == 2:
                mainUrl = self.raw[0]
                self.raw = self.raw[1]
                
                print("ok ",self.raw)
            else:
                self.raw = ""
                mainUrl = self.raw[0]
            print(mainUrl)
            self.mainUrl = mainUrl.split('/')[6]
        else:
            if ":" in mainUrl:
                mainUrl, self.raw = mainUrl.split(':', 1)
            self.mainUrl = mainUrl
        print(self.mainUrl)
        print(self.raw)

g = Zee5("https://www.zee5.com/web-series/details/mukhbir-the-story-of-a-spy/0-6-4z5199975:1:1-1")