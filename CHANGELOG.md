# Changelog

<!--next-version-placeholder-->

## v0.12.2 (2023-07-21)

### Fix

* #38: fix tweet sorting ([`b075eb7`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/b075eb7c93537f8d504f06d6bc9e6f8e72ba2adc))

## v0.12.1 (2023-07-21)

### Fix

* #31: add sentry integration ([`d0754b2`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/d0754b22ccdf928cc02b49c1258b6f8b1aeb0705))

### Documentation

* #35: add demo stand component scheme ([`a748a54`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/a748a54b500cfd49460fdccffd48a016ad0cd9d5))
* Add badges ([`75990b3`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/75990b36894fe328c77a81462fe6848839b82f37))

## v0.12.0 (2023-06-27)

### Feature

* #33 add pagination for tweets ([`af49b50`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/af49b50d0795e22665e5e86f0c675e912edb5c28))

## v0.11.3 (2023-06-27)

### Fix

* Fix form field name for POST /api/medias ([`52b15ba`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/52b15baf9a7bbc73b7b331fd5d25f44703965d2f))

## v0.11.2 (2023-06-27)

### Fix

* Sort tweets also by posted_at ([`15c8fce`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/15c8fce2b3036db70178b197389c48d868a55909))

## v0.11.1 (2023-06-27)

### Fix

* Add CORS policy ([`d240b71`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/d240b71d1a975935fbc5637c30d11ee37c081e51))

## v0.11.0 (2023-06-23)

### Feature

* #13 add route GET /api/users/me and logic ([`52cd745`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/52cd745e2c925989f0a6ea398a9d95139f9d8011))

## v0.10.0 (2023-06-22)

### Feature

* #14: add GET /api/users/{user_id} route and logic ([`636f9fc`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/636f9fca1493bd3c525b4df2c32f5b9af22260b1))

### Documentation

* Update image ([`f39f864`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/f39f86491e9d4161e7ae231d25882b043c1073e1))

## v0.9.2 (2023-06-22)

### Fix

* Add unique_items for NewTweetIn.medias ([`dde8324`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/dde832406cab508e53db50bd57ad5230b912a409))

## v0.9.1 (2023-06-21)

### Fix

* Handle concrete exceptions on POST /api/medias ([`648ff00`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/648ff0038799008dde50118c0d65ef99c3f6af5d))

### Documentation

* Update docs in part of autoreleasing ([`b58a8ef`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/b58a8eff39e8e62f8db2d073643e3c432bdbb1e1))

## v0.9.0 (2023-06-21)

### Feature

* #12: GET /api/tweets return tweets ([`2f01e4f`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/2f01e4f6e92f69a7af7eff442cd888bf8067cc8e))
* #12: add GET /api/tweets with only auth ([`75b3f3d`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/75b3f3d7ab234e545e495cacf67c505000381bcc))

### Fix

* #12: likes in TweetOut must be unique ([`760ab1b`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/760ab1b07b5128114a1b9fc0b42586a7f975829a))
* #12: fix sort by likes ([`8fe6be7`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/8fe6be7de3a1cc829ec18b914f2af1c10f59dd16))

### Documentation

* #12: fix example for TweetListOut model ([`847b892`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/847b892d2c0543747c6020870bc014e0d5647f9f))
* Fix README.md mistakes ([`fecbee2`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/fecbee26993b52607730038b5a84e23fadc22468))

## v0.8.2 (2023-06-19)

### Fix

* Serve static files in debug mode ([`b76e3fd`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/b76e3fdef22e5b8544ddbebf02fdac99e71380e2))
* Commit tweets and medias to DB ([`3e02581`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/3e02581be2cb06e3a8f4c6b707e13e09d7059878))

### Documentation

* #16: describe how to setup SSH keys for GitLab CI/CD ([`36e4a5d`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/36e4a5dcfb3e70244e9fc92b8207be994a22921d))
* #16: update README.md ([`5c91e0b`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/5c91e0b606ed3a82244b85503fe7edc9bc87b8b4))
* #16: update README.md in part of demo stand ([`2789f5b`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/2789f5b7d4127a1cdae9782f65c4ada91e013340))
* #16: update docs for demo stand ([`3986d9c`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/3986d9c945ca71652fa7d4d36e69830454676ffc))
* #16: describe demo stand in README.md ([`6d3dd4d`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/6d3dd4d05f6c7c58bc666e2de1d764d5c7ca7f3a))

## v0.8.1 (2023-06-09)

### Fix

* Fix when 404 early than 401 ([`f112206`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/f112206bf795c258b1363704b3324629bbea6705))

## v0.8.0 (2023-06-09)

### Feature

* #11: add route and logic for user unfollowing ([`de4047a`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/de4047a9b2071d88a552187a67f6197ad41a1c8e))

## v0.7.0 (2023-06-09)

### Feature

* #10: add route and logic for user followings ([`be53b5b`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/be53b5b3d0d32247f14951d66f74a2f2475c9b8b))

### Documentation

* Show actual API version in Swagger ([`bbb57bd`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/bbb57bd857587ba7bf404b4e4b94b8f7ccbaf183))
* Update README.md ([`9650171`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/96501717762be305f2a3bacba7f23dfa7946112f))

## v0.6.0 (2023-06-08)

### Feature

* #9: add unlike route and logic ([`52bb019`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/52bb01946e55f9ed76c0b3a1e0edfdfe0bbe6281))

### Documentation

* Update Swagger docs ([`f44180f`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/f44180f70d1cbe559ff456c3594ecfc5c3020838))

## v0.5.0 (2023-06-07)

### Feature

* #8: add route and logic for like tweets ([`00f76f0`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/00f76f008a1ae14de19b65338621a297e2772fee))

## v0.4.0 (2023-06-06)

### Feature

* #7: add delete tweet logic ([`e4a148f`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/e4a148fc4eed4fa57cc89a7bf70286e6a577eda2))
* #7: add route for delete tweet ([`915698e`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/915698e5697f7a78965fdad850de85bcb783f82d))

### Documentation

* #7: update README.md ([`c3da2ae`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/c3da2aed94480321246262f31c13a47192c69d83))

## v0.3.0 (2023-06-06)

### Feature

* Force increase release version ([`61a7938`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/61a7938c6e7ce29618bd1ccf7cba4389484d56fa))

### Documentation

* Add link to angular commit message styleguide ([`6cd4ed6`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/6cd4ed69591b7503939aacea068d0204ccc6f22f))

## v0.2.0 (2023-06-05)

### Feature

* Merge branch '5-post-api-tweets' into 'master' ([`500ee53`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/500ee5364c83478124c6a5d15f2cd45ed0ebc530))

## v0.1.0 (2023-06-05)

### Feature

* #26: add semantic versioning ([`be889ed`](https://gitlab.skillbox.ru/vladimir_saltykov/python_advanced_diploma/-/commit/be889ed1728a552439843111484251e3f46b62ed))
