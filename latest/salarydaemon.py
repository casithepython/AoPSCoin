import main
import emaildata
import schedule
import time
from datetime import datetime


def job():
    forums = main.get_forum_names()
    for forum in forums:
        deservedScore = main.forum_score(forum)
        currentScore = main.most_recent_balance(forum)
        if deservedScore > currentScore:
            coinsToPay = deservedScore - currentScore
            print(main.transfer("AoPSCoin Central Bank",
                                [forum],
                                coinsToPay,
                                "Automatic payment of " + str(coinsToPay) + " to " + forum + " at " + str(
                                    datetime.now())))
            main.update_most_recent_balance(forum, coinsToPay)
        else:
            emaildata.email(forum + " has not increased their score today")
            print(forum + " has not increased their score today")


schedule.every().day.at("21:39").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)  # wait one minute
