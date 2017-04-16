import re
import scrapy #导入scrapy包
from bs4 import BeautifulSoup
from scrapy.http import Request ##一个单独的request的模块，需要跟进URL的时候，需要用它
from dingdian.items import DingdianItem ##这是我定义的需要保存的字段，（导入dingdian项目中，items文件中的DingdianItem类）




class Myspider(scrapy.Spider):

    name = 'dingdian'
    allowed_domains = ['23us.com']
    bash_url = 'http://www.23us.com/class/'
    bashurl = '.html'

    def start_requests(self):
        for i in range(1, 11):
            url = self.bash_url + str(i) + '_1' + self.bashurl
            yield Request(url, self.parse)
        yield Request('http://www.23us.com/quanben/1', self.parse2)

    def parse(self, response):
        max_num = BeautifulSoup(response.text, 'lxml').find('div', class_='pagelink').find_all('a')[-1].get_text()
        bashurl = str(response.url)[:-7]
        for num in range(1, int(max_num) + 1):
            url = bashurl + '_' + str(num) + self.bashurl
            yield Request(url, callback=self.get_name)

    def parse2(self, response):
        max_num = BeautifulSoup(response.text, 'lxml').find('div', class_='pagelink').find_all('a')[-1].get_text()
        for num in range(1, int(max_num) + 1):
            url = 'http://www.23us.com/quanben/' + str(num)
            yield Request(url, callback=self.get_name)

    def get_name(self, response):
        tds = BeautifulSoup(response.text, 'lxml').find_all('tr', bgcolor="#FFFFFF")
        for td in tds:
            novelname = td.find_all('a')[1].get_text()
            novelurl = td.find_all('a')[1]['href']
            yield Request(novelurl, callback=self.get_chapterurl, meta={'name':novelname, 'url':novelurl}, dont_filter=True)

    def get_chapterurl(self, response):
        item = DingdianItem()
        item['name'] = str(response.meta['name']).replace('\xa0', '')
        item['novelurl'] = response.meta['url']
        soup = BeautifulSoup(response.text, 'lxml')
        #meta 获取方式,不能用find，find_all
        category = soup.find(attrs={'name':'og:novel:category'})['content']
        author = soup.find(attrs={'name':'og:novel:author'})['content']
        name_id = str(response.url)[-6:-1].replace('/', '')
        item['category'] = str(category)
        item['author'] = str(author)
        item['name_id'] = name_id
        yield item
        yield Request( response.url, callback=self.get_chapter, meta={'name':name_id} )


    def get_chapter(self, response):
        urls = re.findall(r'<td class="L"><a href="(.*?)">(.*?)</a></td>', response.text)
        num = 0
        for url in urls:
            num = num + 1
            chapterurl = response.url + url[0]
            chaptername = url[1]
            rets = Sql.sclect_chapter(chapterurl)
            if rets[0] == 1:
                print('章节已经存在了')
                return False
            else:
                yield Request(chapterurl, callback=self.getchaptercontent, meta={'num':num, 'name_id' : response.meta['name'], 'chaptername': chaptername, 'chapterurl':chapterurl})

    def getchaptercontent(self, response):
        item = DcontentItem()
        item['num'] = response.meta['num']
        item['id_name'] = response.meta['name_id']
        item['chaptername'] = str(response.meta['chaptername']).replace('\xa0', '')
        item['chapterurl'] = response.meta['chapterurl']
        content = BeautifulSoup(response.text, 'lxml').find('dd', id='contents').get_text()
        item['chaptercontent'] = str(content).replace('\xa0', '')
        yield item