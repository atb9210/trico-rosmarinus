HTTP POST REQUEST
URL: https://offers.squidbomb.net/forms/api/
Required fields:
uid=019c4347-d9b5-7b2b-8fcc-23443e24b76c
key=38b4aea53d4c8a50135870
offer=258
lp=279
street-address={street-address}
tel={tel}
name={name}
tmfp={FINGERPRINT}*
ip={USER_IP_ADDRESS}  (only if fingerprint is missing)
ua={USER_USERAGENT}  (only if fingerprint is missing)

Optional fields:
utm_source={utm_source}
utm_medium={utm_medium}
utm_campaign={utm_campaign}
utm_term={utm_term}
utm_content={utm_content}
subid={subid}
subid2={subid2}
subid3={subid3}
subid4={subid4}
pubid={pubid}

*Fingerprint: To add the user fingerprint you must:
1. Add to the form an hidden input with name="tmfp"
2. include the following script in the page:
<script src="https://offers.squidbomb.net/forms/tmfp/" crossorigin="anonymous" defer></script>
This script will automatically add the fingerprint to the form data.
 If you add the fingerprint, you don't need to add the ip and user agent fields.
Api Response:
code: 200 in case of success, 4xx in case of errors (required fields missing, user/offer/lp not found, etc.)
message: "OK" or "DOUBLE". If DOUBLE, you should not load the purchase pixel on your "thank you" page
Recommended: FORM CLICK PIXEL
Paste anywhere in the page where the form is displayed. It will count +1 click for every view.
<img src="https://offers.squidbomb.net/forms/api/ck/?o=258&uid=019c4347-d9b5-7b2b-8fcc-23443e24b76c&lp=279" style="width:1px;height:1px;display:none" alt="">

