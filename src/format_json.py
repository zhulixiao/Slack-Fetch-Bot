import json
from datetime import datetime

from src.commons import download_file

def format_json_to_html(*json_files, most_recent_first=True, download_img=True):
    # read the json files and append the data to a list
    data = []
    for json_file in json_files:
        with open(json_file, 'r') as f:
            data.extend(json.load(f)["data"])

    # sort the messages by datetime object created from timestamp string by ascending order
    data = sorted(data, key=lambda x: datetime.strptime(x["ts"], "%Y-%m-%d %H:%M:%S"))
    if most_recent_first:
        data = data[::-1]

    # determine the filename of the html file
    filename = json_files[0].split(".")[0]

    # define the styles
    info_style = "font-family:verdana"
    user_style = "font-size:15px;padding-right:12px"
    ts_style = "font-size:12px;color:gray"
    message_style = "font-family:verdana;font-size:15px;margin-top:-10px"

    # create a new html file and write the data into it
    with open(filename + '.html', 'w') as f:
        for msg in data:
            is_img = False
            # write the user and timestamp
            f.write("<p style='{}'><span style='{}'><b>{}</b></span><span style='{}'>{}</span></p>"
                    .format(info_style, user_style, msg["user"], ts_style, msg["ts"]))

            # write the image if there is one
            if download_img:
                for token in msg["message"].split():
                    if token.startswith("https") and (token.endswith(".jpg") or token.endswith(".png")):
                        is_img = True
                        img_name = token.strip().split("/")[-1]
                        download_file(token, img_name)
                        # find the image from conversation_history folder with width 300
                        f.write("<img src='downloaded_files/{}' width='300'>".format(img_name))
                        
            # write the message text
            if not is_img:
                f.write("<p style='{}'>{}</p>".format(message_style, msg["message"]
                                                      .replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")))

