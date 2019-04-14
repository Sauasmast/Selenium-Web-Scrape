from selenium import webdriver
from bs4 import BeautifulSoup
import csv
import datetime


def scrape():
    ''' This method is used to scrape the data out the german website for the data information.
    For further insight and future reference see the document web structure.'''

    # Instantiating a web browser(You can use chrome if you want its right on the working directory)
    browser = webdriver.Firefox(executable_path="./geckodriver")

    # Make a new csv file to write
    with open('data.csv', 'w+') as new_file:
        writer = csv.writer(new_file)
        writer.writerow(["Date", "Plan Name", "Provider", "Signal Price",
                            "Average Monthly Cost", "Data_MB", "Call Minutes", "SMS"])

    # open the csv file written above to append data onto it. 
    with open('data.csv', 'a') as write_file:
        writer = csv.writer(write_file)

        # For scraping all of the eight pages.
        for i in range(1, 9):
            url = ('''https://www.preis24.de/handy-flatrate-vergleich/?mobiletariffCalculatorForm=
                    true&mergeDefaults=false&productType=mobile&sortBy=monthlyEffectiveCost
                    &sortDirection=up&partnerId=1665&telephony=&telephonyMinutePackageMin=50
                    &numberPorting=any&sms=&smsPackageMin=50&internetVolumeMin=
                    &maxDownloadSpeedKb=&maxCostsMonth=&deviceType=none&maxCostsHardwareOnce=150
                    &network%5B%5D=1&network%5B%5D=2&network%5B%5D=4&carrier=&maxTariffsPerProvider=
                    &type=vertrag&maxContractRuntime=&customerGroup=&simCardType=&signupAvailableOnly=true&page={}'''.format(i))
            browser.get(url)
            soup = BeautifulSoup(browser.page_source, "lxml")

            # with open('scrape.html') as html_file:
            #     soup = BeautifulSoup(html_file, "lxml")

            # all the prices are included in the ul as a li with class of cms-widget_calculator_result_list
            ul_element = soup.find("ul", class_="cms-widget_calculator_result_list")

            # get all of the li element within a ul tag - all the childrens
            all_list_tags = ul_element.findChildren("li", recursive=False)

            for each_li_tags in all_list_tags:
                # within each li tags there will exist the div tag with the class cms-widget_calculator_result_list_offer
                # each of the div class will have an three different div tags with the three important data (average price, plan and talktime) needed
                container_div = each_li_tags.find(
                    "div", class_="cms-widget_calculator_result_list_offer")
                # In between the site has a list with the ads therefore checking the container
                if (container_div != None):
                    # Main container with information about - average monthly cost, plan name, provider name, data, minutes and sms data
                    # First for the average price tag
                    average_price_month_div = container_div.find(
                        "div", class_="cms-widget_calculator_result_list_price")
                    average_price_month_span = average_price_month_div.find(
                        "div", "cms-widget_calculator_result_list_price-effective")
                    average_price_month = average_price_month_span.find(
                        "span", class_="cms-widget_calculator_result_list_price_amount")['content']

                    # Second for the plan name and provider name
                    plan_provider_name_div = container_div.find(
                        "div", class_="cms-widget_calculator_result_list_product")
                    plan_provider_name_within_div = plan_provider_name_div.find(
                        "div", class_="cms-widget_calculator_result_list_provider")
                    plan_provider_name = plan_provider_name_within_div.find(
                        "div", class_="cms-widget_calculator_result_list_offer-name").text
                    list_plan_provider = plan_provider_name.strip().split("\n")
                    plan_name = list_plan_provider[0].strip()
                    provider_name = list_plan_provider[1].strip()

                    # Third div for the data and minutes record
                    data_info_container = container_div.find(
                        "div", class_="cms-widget_calculator_result_list_item-container")
                    data_info_div = list((filter(lambda x: x != "", data_info_container.find(
                        "div", class_="cms-widget_calculator_result_list_item-wrapper").text.lstrip().split("\n"))))
                    data_info_div = list(
                        map(lambda x: x.strip(), data_info_div))
                    # Filters the data on the basis of the length of the div 
                    # Some has sms, some has call and some has data (It depends)
                    data_returned = filter_call_data(data_info_div)
                    data_minutes, data_sms, data_internet = data_returned[0], data_returned[1], data_returned[2]

                    # This is a sepearate tag with the hiddden accordion. It is required for the signal price.
                    # Get the average price from the accordion table
                    accordion_container = each_li_tags.find(
                        "div", class_="cms-widget_calculator_result_list_moreinformation")
                    accordion_tab = accordion_container.find(
                        "div", class_="cms_tab")
                    accordion_list = accordion_tab.find(
                        "ul", class_="cms_accordion")
                    accordion_second_tab = accordion_list.findChildren("li", recursive=False)[
                        1]
                    average_value = accordion_second_tab.find_all(
                        "table")[1].tr.select("td:nth-child(3)")[0].text.strip()
                    # Getting rid of the pound sign and replacing comma with .
                    signal_price = average_value.split(
                        " ")[0].replace(",", ".")

                    # Write into the csv file
                    writer.writerow([datetime.date.today().strftime(
                        '%Y/%m/%d'), plan_name, provider_name, signal_price, average_price_month, data_internet, data_minutes, data_sms])

def filter_call_data(data):
    ''' This function is responsible for distinguish the talktime, SMS and internet data '''

    # The given list can have 8 element in which case data are in sequence. 
    if (len(data) == 8):
        data_minutes = check_unit_talktime(data[0:2])
        data_sms = data[2].strip()
        data_internet = check_unit_internet(data[4])
    # The given list can have 6 element in which case first data might be sms or talktime. 
    elif(len(data) == 6):
        if data[1] == "SMS":
            data_minutes = None
            data_sms = data[0]
        else:
            data_minutes = check_unit_talktime(data[0:2])
            data_sms = None
        data_internet = check_unit_internet(data[2])
    # The given list have the length of 4 in which case it will not have both sms or talktime. 
    else:
        data_minutes = None
        data_sms = None
        data_internet = check_unit_internet(data[0])
    return ([data_minutes, data_sms, data_internet])
    
def check_unit_talktime(data):
    ''' This function is responsible for assigning the correct units to the talk time data '''
    if data[1] == "Minuten":
        return (data[0]+" minutes")
    elif data[1] == "heiten":
        return (data[0].split(" ")[0]+ " units")
    else:
        return(data[0])

def check_unit_internet(data):
    ''' This functions converts the data time into MB format (float) since csv will not read 
    .0, it can be converted into int. This funcitons also makes sure the data exist if it 
    does not it sends the 0 data'''
    data_numerical = data.split(" ")[0]
    try:
        data_numerical = float(data_numerical.strip())
    except ValueError:
        data_numerical = 0

    if("GB" in data):
        converted_data = data_numerical * 1024
    else:
        converted_data = data_numerical
    return converted_data

if __name__ == "__main__":
    scrape()
