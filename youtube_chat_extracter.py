from bs4 import BeautifulSoup
import requests
import re
import sys
import os.path

headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 '}
youtube_id = "UYKRKyitmw4"
youtube_url = "https://www.youtube.com/watch?v="
continuation_url = "https://www.youtube.com/live_chat_replay?continuation="
session = requests.Session()

def get_chat_comments(youtube_id):
	# 元動画からHTML抽出
	top_html = session.get(youtube_url + youtube_id, headers=headers)
	top_soup = BeautifulSoup(top_html.text, "html.parser")

	# 一番目のチャットデータ取得
	# 一番初めだけ末尾のconstinuation dataを使用してチャット取得
	script = top_soup.find_all("script", text=re.compile("\"continuations\":"))
	continuations = re.findall("\"continuation\":\"([^\"]*)", str(script))
	html = session.get(continuation_url + continuations[-1], headers=headers)
	soup = BeautifulSoup(html.text, "lxml")

	# データ整形
	for scrp in soup.find_all("script"):
		if "window[\"ytInitialData\"]" in scrp.text:
			dict_str = scrp.text.split(" = ",1)[1]

	dict_str = dict_str.replace("false","False")
	dict_str = dict_str.replace("true","True")
	dict_str = dict_str.rstrip("  \n;")
	dict_data = eval(dict_str)

	# コメント取得
	# comment_data_list = [{"comment", "author", "paid", "time"}, ... ]
	# comment = ["replayChatItemAction"]["actions"][0]["addChatItemAction"]["item"]["liveChatTextMessageRenderer"]["message"]["runs"]
	# paid_comment = ["replayChatItemAction"]["actions"][0]["addChatItemAction"]["item"]["liveChatPaidMessageRenderer"]["message"]["runs"]
	# author = ["replayChatItemAction"]["actions"][0]["addChatItemAction"]["item"]["liveChatTextMessageRenderer"]["authorName"]["simpleText"]
	# paid_author = ["replayChatItemAction"]["actions"][0]["addChatItemAction"]["item"]["liveChatPaidMessageRenderer"]["authorName"]["simpleText"]
	# paid = ["replayChatItemAction"]["actions"][0]["addChatItemAction"]["item"]["liveChatPaidMessageRenderer"]["purchaseAmountText"]["simpleText"]
	# time = ["replayChatItemAction"]["videoOffsetTimeMsec"]
	comments_data_list = []
	comments_error_list = []
	for actions_data in dict_data["continuationContents"]["liveChatContinuation"]["actions"][1:]:
		comment_data = {}
		try:
			paid_comments = actions_data["replayChatItemAction"]["actions"][0]["addChatItemAction"]["item"]["liveChatPaidMessageRenderer"]["message"]["runs"]
			paid_comment = ""
			for c in paid_comments:
				try:
					paid_comment += c["text"]
				except:
					try:
						paid_comment += "[{}]".format(c["emoji"]["emojiId"])
					except:
						print("GET ERROR KEYWORD: {}".format(c))
			comment_data["comment"] = paid_comment
			comment_data["author"] = actions_data["replayChatItemAction"]["actions"][0]["addChatItemAction"]["item"]["liveChatPaidMessageRenderer"]["authorName"]["simpleText"]
			comment_data["paid"] = actions_data["replayChatItemAction"]["actions"][0]["addChatItemAction"]["item"]["liveChatPaidMessageRenderer"]["purchaseAmountText"]["simpleText"]
		except:
			try:
				comments = actions_data["replayChatItemAction"]["actions"][0]["addChatItemAction"]["item"]["liveChatTextMessageRenderer"]["message"]["runs"]
				comment = ""
				for c in paid_comments:
					try:
						comment += c["text"]
					except:
						try:
							comment += "[{}]".format(c["emoji"]["emojiId"])
						except:
							print("GET ERROR KEYWORD: {}".format(c))
				comment_data["comment"] = comment
				comment_data["author"] = actions_data["replayChatItemAction"]["actions"][0]["addChatItemAction"]["item"]["liveChatTextMessageRenderer"]["authorName"]["simpleText"]
			except:
				comments_error_list.append(str(actions_data))
				continue

		time_ms = actions_data["replayChatItemAction"]["videoOffsetTimeMsec"]
		time_s = int(time_ms)/1000
		comment_data["time"] = time_s
		comments_data_list.append(str(comment_data))

	# 次のチャットデータ取得
	while(1):
		try:
			next_continuation = dict_data["continuationContents"]["liveChatContinuation"]["continuations"][0]["liveChatReplayContinuationData"]["continuation"]
			print(next_continuation)
			html = session.get(continuation_url + next_continuation, headers=headers)
			soup = BeautifulSoup(html.text, "lxml")

			for scrp in soup.find_all("script"):
				if "window[\"ytInitialData\"]" in scrp.text:
					dict_str = scrp.text.split(" = ",1)[1]

			dict_str = dict_str.replace("false","False")
			dict_str = dict_str.replace("true","True")
			dict_str = dict_str.rstrip("  \n;")
			dict_data = eval(dict_str)

			# コメント取得
			for actions_data in dict_data["continuationContents"]["liveChatContinuation"]["actions"][1:]:
				comment_data = {}
				try:
					paid_comments = actions_data["replayChatItemAction"]["actions"][0]["addChatItemAction"]["item"]["liveChatPaidMessageRenderer"]["message"]["runs"]
					paid_comment = ""
					for c in paid_comments:
						try:
							paid_comment += c["text"]
						except:
							try:
								paid_comment += "[{}]".format(c["emoji"]["emojiId"])
							except:
								print("GET ERROR KEYWORD: {}".format(c))
					comment_data["comment"] = paid_comment
					comment_data["author"] = actions_data["replayChatItemAction"]["actions"][0]["addChatItemAction"]["item"]["liveChatPaidMessageRenderer"]["authorName"]["simpleText"]
					comment_data["paid"] = actions_data["replayChatItemAction"]["actions"][0]["addChatItemAction"]["item"]["liveChatPaidMessageRenderer"]["purchaseAmountText"]["simpleText"]
				except:
					try:
						comments = actions_data["replayChatItemAction"]["actions"][0]["addChatItemAction"]["item"]["liveChatTextMessageRenderer"]["message"]["runs"]
						comment = ""
						for c in paid_comments:
							try:
								comment += c["text"]
							except:
								try:
									comment += "[{}]".format(c["emoji"]["emojiId"])
								except:
									print("GET ERROR KEYWORD: {}".format(c))
						comment_data["comment"] = comment
						comment_data["author"] = actions_data["replayChatItemAction"]["actions"][0]["addChatItemAction"]["item"]["liveChatTextMessageRenderer"]["authorName"]["simpleText"]
					except:
						comments_error_list.append(str(actions_data))
						continue

				time_ms = actions_data["replayChatItemAction"]["videoOffsetTimeMsec"]
				time_s = int(time_ms)/1000
				comment_data["time"] = time_s
				comments_data_list.append(str(comment_data))
		except:
			break

	return comments_data_list


if __name__=="__main__":
	args = sys.argv
	if len(args) == 2:
		fname = os.path.splitext(os.path.basename(args[1]))[0].split("_")
		data = get_chat_comments(fname[1])

		with open("youtube_comments_" + fname[0], "w") as f:
			f.write(str(data))
	else:
		print("need an argument such as outputFilename_youtubeId.mp4")
