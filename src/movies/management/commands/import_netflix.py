from collections import defaultdict
from datetime import datetime
from typing import Literal

import dateutil
import requests
from django.core.management.base import BaseCommand
from requests.exceptions import HTTPError

from movies.models import MotnShow, UserViewInteraction

# curl 'https://www.netflix.com/api/aui/pathEvaluator/web/%5E2.0.0?method=call&callPath=%5B%22aui%22%2C%22viewingActivity%22%2C1%2C50%5D&falcor_server=0.1.0'   -H 'accept: */*'   -H 'accept-language: en-US,en;q=0.9,nl;q=0.8,de;q=0.7'   -H 'cache-control: no-cache'   -H 'content-type: application/x-www-form-urlencoded'   -b 'nfvdid=BQFmAAEBEGsRqAgQBAI2u5tLa0X8uzFgIrmGaLUKhuAewvn_8SjQMSiCHAocERQHCmtNsdv6fFBsBeFWyP2FVQ7ysKta9v885_eyOnF7LxZyrwrQ8ZPXp1GxFiXpgPY81ZgSX9ti86HrMSJFdgnunFXQVMDsJQNr; OptanonAlertBoxClosed=2025-11-13T00:14:14.156Z; netflix-sans-normal-3-loaded=true; netflix-sans-bold-3-loaded=true; profilesNewSession=0; flwssn=9f4d2e9b-8c76-4be3-a02c-c0622379efd7; gsid=b8a2a265-f9c5-4efb-81c6-29b1f5736f33; SecureNetflixId=v%3D3%26mac%3DAQEAEQABABQf9sF9VNHnEEQvOFDZqeFwVsz0nEv8xvY.%26dt%3D1764945004732; NetflixId=v%3D3%26ct%3DBgjHlOvcAxL1AsywgaIaMlxpaAfDWHr6ayMCLImu8Qz8ud7L0KLVe7RIyGOKS8uYU3SQo5jgBl72k94eKO6pnicKBzMkT6EGkcFAsim9ChAZJAULNA6V3ZDFZrJmtgBgSdJQFfCed0c6eQw9c7asU-83dztbYPfdPZ9l65ncDwRGM7UI0KQnU1_rYGbXKS1N64DkWaV72JYFzLbDQXwb7gF_8U4B0DJsICa0pMaz4wjle7DBZ4cDNOQJyL8VSh_D5NWei8TFhJnOdVdmRWwFXyfF7OdNwAVVYYFYoqblg1Ge2P5U6CTxDhaTqzFAVs4HmvoMyywMhoaRbOmtXA7bClWi4cawuVdHAsmsMVWHc6gyWxiduckoXUM7mYJQ0Il7MuwlQcA1QS8EQd1x8ZfWxlpn7ANTWwwIvMR7Gj4_vIf8Q8kUKEnU9JjxKylT4-IEQs3N5klCp03qsPwjnFUyFkbL9dyrvhDqu9YMTyyXikgNeu9cG3DYF2ljsx_mriwYBiIOCgw8neJK8bFkthmA2rc.%26pg%3DOA3XCIAX6BEUHISQK3LYM3FQGQ%26ch%3DAQEAEAABABSzW0KUOP7MjPeOxGHHP6D8MYLJ10NaRHg.; pas=%7B%22supplementals%22%3A%7B%22muted%22%3Atrue%7D%7D; dsca=customer; OptanonConsent=isGpcEnabled=0&datestamp=Fri+Dec+05+2025+15%3A30%3A57+GMT%2B0100+(Central+European+Standard+Time)&version=202510.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=b889060c-b658-4477-9e60-7a3f84423fea&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A0&intType=6&geolocation=NL%3BNH&AwaitingReconsent=false'   -H 'origin: https://www.netflix.com'   -H 'pragma: no-cache'   -H 'priority: u=1, i'   -H 'referer: https://www.netflix.com/settings/viewed/WRDQKKRKUZAPRD4A4XAPBLS56E'   -H 'sec-ch-ua: "Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"'   -H 'sec-ch-ua-mobile: ?0'   -H 'sec-ch-ua-model: ""'   -H 'sec-ch-ua-platform: "Linux"'   -H 'sec-ch-ua-platform-version: ""'   -H 'sec-fetch-dest: empty'   -H 'sec-fetch-mode: cors'   -H 'sec-fetch-site: same-origin'   -H 'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'   -H 'x-netflix.browsername: Chrome'   -H 'x-netflix.browserversion: 142'   -H 'x-netflix.client.request.name: ui/xhrUnclassified'   -H 'x-netflix.clienttype: akira'   -H 'x-netflix.esnprefix: NFCDCH-LX-'   -H 'x-netflix.nq.stack: prod'   -H 'x-netflix.osfullname: Linux'   -H 'x-netflix.osname: Linux'   -H 'x-netflix.osversion: 0.0.0'   -H 'x-netflix.request.attempt: 1'   -H 'x-netflix.request.client.context: {"appstate":"foreground"}'   -H 'x-netflix.request.id: ef45ba14ce8744c7adae87df5976a7c6'   -H 'x-netflix.request.routing: {"path":"/nq/aui/endpoint/%5E1.0.0-web/pathEvaluator","control_tag":"auinqweb"}'   -H 'x-netflix.uiversion: vf4f1656a'   --data-raw 'param=%7B%22guid%22%3A%22WRDQKKRKUZAPRD4A4XAPBLS56E%22%7D'  # noqa: E501

url = "https://www.netflix.com/api/aui/pathEvaluator/web/%5E2.0.0"

params = {
    "method": "call",
    "callPath": '["aui","ratingHistory",1,50]',
    "falcor_server": "0.1.0",
}

headers = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9,nl;q=0.8,de;q=0.7",
    "cache-control": "no-cache",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://www.netflix.com",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://www.netflix.com/settings/viewed/WRDQKKRKUZAPRD4A4XAPBLS56E",
    "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"Linux"',
    "sec-ch-ua-platform-version": '""',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",  # noqa: E501
    "x-netflix.browsername": "Chrome",
    "x-netflix.browserversion": "142",
    "x-netflix.client.request.name": "ui/xhrUnclassified",
    "x-netflix.clienttype": "akira",
    "x-netflix.esnprefix": "NFCDCH-LX-",
    "x-netflix.nq.stack": "prod",
    "x-netflix.osfullname": "Linux",
    "x-netflix.osname": "Linux",
    "x-netflix.osversion": "0.0.0",
    "x-netflix.request.attempt": "1",
    "x-netflix.request.client.context": '{"appstate":"foreground"}',
    "x-netflix.request.id": "c3036647cf234595bf95e2fc228fc54b",
    "x-netflix.request.routing": '{"path":"/nq/aui/endpoint/%5E1.0.0-web/pathEvaluator","control_tag":"auinqweb"}',
    "x-netflix.uiversion": "vf4f1656a",
}

cookies = {
    "accept-language": "en-US,en;q=0.9",
    "authorization": "Bearer 1733496025346.8r8zsdv6fFBsBeFWyP2FVQ7ysKta9v885_eyOnF7LxZyrwrQ8ZPXp1GxFiXpgPY81ZgSX9ti86HrMSJFdgnunFXQVMDsJQNr",  # noqa: E501
    "cache-control": "no-cache",
    "OptanonAlertBoxClosed": "2025-11-13T00:14:14.156Z; ",
    "netflix-sans-normal-3-loaded": "true; ",
    "netflix-sans-bold-3-loaded": "true; ",
    "flwssn": "9f4d2e9b-8c76-4be3-a02c-c0622379efd7; ",
    "gsid": "b8a2a265-f9c5-4efb-81c6-29b1f5736f33; ",
    "pas": "%7B%22supplementals%22%3A%7B%22muted%22%3Atrue%7D%7D; ",
    "cookie": "nfvdid=BTV-11a58e60-f131-40e1-b4f0-45c1108253a6; NetflixId=v%3D3%26ct%3DBgjHlOvcAxKCA5WmaVSblJIDTEo_C3wMDkQF35Qrq5xN0wq1U3UJ2R8SGn3Q3h9uoCDYB3TvmB3EVZFYABrYmfxUpl8JBxQF7q0kSwYZFkQggpsSUTjWD487bnOHX0imHF5nGul_DNbfvgOJioMVeY-kQbrdhbeBJKLnIP5cfmblG5YrF16HsL05Mg098sTDmsmhNH4PQ1Wi0oOGSPj2tF5U_zPReFy6H6xTLFtSBhZjOOTwpbNFOKKyOy9ozGW0CqNlFz3NiUZM5LOHDDNAU5VmuRe5KACIvr7aNdTNixMrBEwSrcWHcF2eflA6CpFIMc2DIv4dTfJXU6nGL2YTuFneD-hAJKLYWV54sStSSTNQO4Vtky5WrvLLyFqGcsefoZYujQzd98gy8V2WMx-iNjEx3MUA0uIoDMdTsKKwhhDG6UFmShxcujxxIVYtiibO1hvLHsEuZzZaNvn1DochspFlWG_8IX5ZxTdZR0cw7b9UbYDTYs50epTBl1T-cXkxnSeYFkhBdTMhO-I5GAYiDgoMNzmRnSY5x38zsz4f%26pg%3DWRDQKKRKUZAPRD4A4XAPBLS56E%26ch%3DAQEAEAABABTpzR3UsYWjKYVrtsQAIqTUjAjXHowgyS8.; profilesNewSession=0; memclid=61fa2d02-1250-424a-ba62-09439c277732; clid=1733496056581%7C61fa2d02-1250-424a-ba62-09439c277732; OptanonConsent=isGpcEnabled=0&datestamp=Sat+Dec+06+2025+15%3A40%3A56+GMT%2B0100+(Central+European+Standard+Time)&version=202510.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=b889060c-b658-4477-9e60-7a3f84423fea&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A0&intType=6&geolocation=NL%3BNH&AwaitingReconsent=false",  # noqa: E501
    "dnt": "1",
}

data = {"param": '{"guid":"WRDQKKRKUZAPRD4A4XAPBLS56E"}'}


def paginated_request(activity: Literal["viewingActivity", "ratingHistory"]):
    page = 0
    total_items = 0
    current_params = params.copy()
    item_name = "ratingItems" if activity == "ratingHistory" else "viewedItems"
    while True:
        current_params["callPath"] = f'["aui","{activity}",{page},50]'
        response = requests.post(url, params=current_params, headers=headers, cookies=cookies, data=data)
        try:
            response.raise_for_status()
        except HTTPError as e:
            print(f"Error {e.status_code}: {e.response.text}")
            break

        json_response = response.json()
        try:
            items = json_response["jsonGraph"]["aui"][activity]["value"][item_name]
        except KeyError:
            raise  # TODO

        if not items:
            break

        yield from items

        total_items += len(items)
        page += 1

    print(f"Fetched {total_items} {item_name} from Netflix")


class Command(BaseCommand):
    def handle(self, *args, **options):
        user_id = 1

        ratings = defaultdict(dict)
        for item in paginated_request("viewingActivity"):
            movie_id = item.get("series") or item.get("movieID")  # Always series ID over episode ID
            current = ratings[movie_id]
            current["title"] = item.get("seriesTitle") or item.get("title")
            date = datetime.fromtimestamp(item.get("date") // 1000).date()
            if not current.get("first_date") or current.get("first_date") > date:
                current["first_date"] = date
            if not current.get("last_date") or current.get("last_date") < date:
                current["last_date"] = date
            try:
                current["viewed_amount"] += 1
            except KeyError:
                current["viewed_amount"] = 1

        for rating_item in paginated_request("ratingHistory"):
            movie_id = rating_item.get("movieID")
            try:
                current = ratings[movie_id]
                new = False
            except KeyError:
                current = {}
                new = True
            if not current.get("title"):
                current["title"] = rating_item.get("title")
            if not current.get("first_date"):
                current["first_date"] = dateutil.parser.parse(rating_item.get("date")).date()
            rating_str = rating_item["reactionRatings"]["thumbs"]

            if rating_str == "THUMBS_WAY_UP":
                rating = 1
            elif rating_str == "THUMBS_UP":
                rating = 1
            elif rating_str == "THUMBS_DOWN":
                rating = -1
            else:
                raise ValueError(f"Unknown rating: {rating_str}")
            current["rating"] = rating

            if new:
                ratings[movie_id] = current

        for key, item in ratings.items():
            try:
                motn = MotnShow.objects.get(source_id=key)
            except MotnShow.DoesNotExist:
                print(f"Count not find MotnShow for {item['title']} by source_id={key}, skipping.")
                continue

            UserViewInteraction.objects.update_or_create(
                user_id=user_id,
                show_id=motn.id,
                defaults={
                    "viewed_amount": item.get("viewed_amount", 1),
                    "completion_ratio": item.get("viewed_amount", 1) / (motn.episode_count or 1.0),
                    "first_date": item.get("first_date"),
                    "last_date": item.get("last_date"),
                    "rating": item.get("rating"),
                },
            )
