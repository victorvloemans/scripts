import requests
import json5
import re
import sys
import argparse

base_url = 'https://techpays.eu'

def print_compensation(job_title, country_plus_job_title_url, output_file=''):
    compensation_url = base_url + country_plus_job_title_url

    headers = {
            'Accept': 'application/json'
    }

    response = requests.request('GET', compensation_url, headers=headers)

    list_key = 'COMPENSATION_LIST'
    list_start = response.text.index(list_key)
    list_end = response.text.index('];', list_start)

    compensation_list = response.text[(list_start+len(list_key)+3): list_end+1]
    compensation_dict = json5.loads(compensation_list)

    output = sys.stdout
    if output_file:
        output = open(output_file, "a")

    emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               "]+", flags=re.UNICODE)

    for compensation in compensation_dict:

        print(emoji_pattern.sub(r'', job_title).strip() + '\t' + emoji_pattern.sub(r'', compensation['companyName']).strip() + '\t' + \
        emoji_pattern.sub(r'', compensation['title']).strip() + '\t' + compensation['totalCompensation'] + '\t' + \
        str(compensation['totalCompensationNumber']) + '\t' + compensation['totalCompensationDetails'] + '\t' + \
        compensation['baseSalary'] + '\t' + str(round(compensation['baseSalaryNumber']/12)).strip(), file=output)

    if output is not sys.stdout:
        output.close()

def list_countries():
    headers = {
            'Accept': 'application/json'
    }

    response = requests.request('GET', base_url, headers=headers)

    menu_start_key = 'id="countriesMenu"'
    menu_end_key_reg = r'</div>\s*</div>'

    country_start_key = '<a href="'
    country_end_key = '"'
    country_name_html_element = 'p'

    countries = []

    list_start = response.text.index(menu_start_key)
    list_end = re.search(menu_end_key_reg, response.text[list_start:]).start()
    countries_list_html = response.text[list_start: list_start+list_end]

    has_countries = True
    while has_countries:
        try:
            country_url_start = countries_list_html.index(country_start_key)
        except:
            break

        country_url_end = countries_list_html.index(country_end_key, country_url_start+len(country_start_key))
        country_url = countries_list_html[country_url_start+len(country_start_key): country_url_end]

        country_name_start = countries_list_html.index('>', countries_list_html.index('<' + country_name_html_element))+1
        country_name_end = countries_list_html.index('</' + country_name_html_element, country_name_start)
        country_name = countries_list_html[country_name_start: country_name_end].strip()

        countries.append({'name': country_name, 'url': country_url})
        countries_list_html = countries_list_html[country_name_end+1:]

    return countries

def list_jobs(country_url):
    request_url = base_url + country_url

    headers = {
            'Accept': 'application/json'
    }

    response = requests.request('GET', request_url, headers=headers)

    menu_start_key = 'id="jobFamilyFilterOptions"'
    menu_end_key_reg = r'</div>\s*</div>'

    job_start_key = '<a href="'
    job_end_key = '"'
    job_name_html_element = 'a'

    jobs = []

    list_start = response.text.index(menu_start_key)
    list_end = re.search(menu_end_key_reg, response.text[list_start:]).start()
    job_list_html = response.text[list_start: list_start+list_end]

    has_jobs = True
    while has_jobs:
        try:
            job_url_start = job_list_html.index(job_start_key)
        except:
            break

        job_url_end = job_list_html.index(job_end_key, job_url_start+len(job_start_key))
        job_url = job_list_html[job_url_start+len(job_start_key): job_url_end]

        job_name_start = job_list_html.index('>', job_url_end+1)+1
        job_name_end = job_list_html.index('</' + job_name_html_element, job_name_start)
        job_name = job_list_html[job_name_start: job_name_end].strip()
        job_name = re.sub('&\w+;', '', job_name)

        jobs.append({'name': job_name, 'url': job_url})
        job_list_html = job_list_html[job_name_end+1:]

    return jobs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='List compensation from techpays.eu. When no command line options are provided these are interactively requested.')
    parser.add_argument('-c', '--country', type=str, default='', help='Name (or unique substring) of country to list')
    parser.add_argument('-n', '--name', type=str, default='', help='Names (or unique substrings) of jobs to list, comma separated')
    parser.add_argument('-o', '--output', type=str, default='', help='Name of output file to append job compensations')
    args = parser.parse_args()

    countries = list_countries()
    selected_country_index = 0

    if args.country:
        for country in countries:
            if country['name'].lower().find(args.country.lower().strip()) >= 0:
                selected_country_index = countries.index(country)
    else:
        for country in countries:
            print('[' + str(countries.index(country)+1) + '] ' + country['name'])

        selected_country_index = int(input('Select country index ')) - 1
        if selected_country_index > len(countries) - 1 or selected_country_index < 0:
            print('Invalid country index')
            sys.exit(0)

        print('')

    jobs = list_jobs(countries[selected_country_index]['url'])

    if args.name:
        job_names = args.name.split(',')
        for job_name in job_names:
            for job in jobs:
                if job['name'].lower().find(job_name.strip().lower()) >= 0:
                    print_compensation(job['name'], job['url'], args.output)
    else:
        for job in jobs:
            print('[' + str(jobs.index(job)+1) + '] ' + job['name'] + ' ' + job['url'])

        selected_job_index = int(input('Select job index ' )) - 1
        if selected_job_index > len(jobs) - 1 or selected_job_index < 0:
            print('Invalid job index')
            sys.exit(0)

        print_compensation(jobs[selected_job_index]['name'], jobs[selected_job_index]['url'], args.output)
