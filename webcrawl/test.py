import csv

urls = []

with open('output0.csv', mode='r') as file:
    reader = csv.reader(file)
    for row in reader:
        url = row[0]  # Assuming the url is in the third column (index 2)
        urls.append(url)
print(urls)