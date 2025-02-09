from urllib.parse import urljoin
import scrapy
import re  

class MoviesInfoParser(scrapy.Spider):
    name = "movie_scraper"
    start_urls = ["https://ru.wikipedia.org/wiki/Категория:Фильмы_по_алфавиту"]
    custom_settings = {'ROBOTSTXT_OBEY': False}

    def parse(self, response):
        base_url = response.url
        movie_page_links = response.xpath("//*[@id='mw-pages']/div/div/div/ul/li/a/@href").getall()
        
        for page in movie_page_links: 
            page_link = urljoin(base_url, page)
            yield response.follow(page_link, self.info_parse)

        pagination_link = response.xpath("//a[contains(text(), 'Следующая страница')]/@href").get()
        if pagination_link:
            next_page_url = urljoin(base_url, pagination_link)
            yield response.follow(next_page_url, self.parse)


    def info_parse(self, response):
        movie_info = {'title': None, 'genres': [], 'year': None, 'director': [], 'country': []}

        quote = response.css("table.infobox")
        movie_info['title'] = quote.css("th.infobox-above::text").get(default="Неизвестно").strip()

        for row in response.xpath("/html/body/div[3]/div[3]/div[5]/div[1]/table[1]/tbody/tr"):
            attribute = row.xpath("th//text()").get()
            if attribute:
                attribute = attribute.strip()
            else:
                continue

            values = [line.strip().replace(',', '') for line in row.xpath("td//text()").getall() if line.strip()]
            filtered_values = [value for value in values if not value.startswith('[') and value != '']
            value = ",".join(filtered_values)

            if 'Жанр' in attribute or 'Жанры' in attribute:
                movie_info['genres'] = [genre.strip() for genre in value.split(",") 
                                    if len(genre.strip()) > 2 and genre not in ['1', ']', 'и']]

            elif attribute == 'Год':
                year = value.split(",")[0]  # берем только первую дату
                if not year.isdigit():  # если год не числовой, заменяем на "Неизвестно"
                    year = "Неизвестно"
                movie_info['year'] = year

            elif attribute in ['Режиссёр', 'Режиссёры']:
                cleaned_value = re.sub(r'<[^>]+>', '', value)  # удаляем HTML-теги
                cleaned_value = re.sub(r'\.mw[\w-]*', '', cleaned_value)  # удаляем CSS-классы
                movie_info['director'] = [director.strip() for director in cleaned_value.split(",") 
                                        if len(director.strip()) > 2 and not director.strip().isdigit()]

            elif attribute in ['Страна', 'Страны']:
                movie_info['country'] = [country.strip() for country in value.split(",") 
                                        if len(country.strip()) > 2 and not country.strip().isdigit()]

        # Если поля пустые, заменяем их на "Неизвестно"
        if not movie_info['genres']:
            movie_info['genres'] = ["Неизвестно"]
        if not movie_info['year']:
            movie_info['year'] = "Неизвестно"
        if not movie_info['director']:
            movie_info['director'] = ["Неизвестно"]
        if not movie_info['country']:
            movie_info['country'] = ["Неизвестно"]

        # выводим информациюю
        yield {
            'title': movie_info['title'],
            'genres': ", ".join(movie_info['genres']),
            'director': ", ".join(movie_info['director']),
            'country': ", ".join(movie_info['country']),
            'year': movie_info['year'],
        }