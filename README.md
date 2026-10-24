# spiral-knights-i18n
Internationalization bundles for Spiral Knights

## How it works
We will occasionally publish new English translations here.

We will accept pull requests for other languages, including new ones.

Then these translations will make their way into the game.

### Fine details

If a translation doesn't need to change it can be omitted from a bundle and the English
version will be used.

The properties files need to be well-formatted and readable by Java. Characters above 127
should be escaped by using `\u00e7` convention.

Run `python3 tools/check_bundles.py` before sending a pull request. It reports keys that
aren't in the English bundle, unescaped characters, and placeholders, HTML tags or `|`
separators that don't match the English. To check only one language, pass it with `--lang`,
e.g. `python3 tools/check_bundles.py --lang es`, and to check only one bundle, use `--bundle`,
e.g. `--bundle pvp`. They can be combined: `--bundle pvp --lang es`.

## License and contributions

### Ownership

Copyright © Grey Havens. All rights reserved.

Spiral Knights, and all text, translations and other material in this repository, are
the property of Grey Havens. "Spiral Knights" and its logos are trademarks of Grey Havens.
This repository is made public only so that people can view it and contribute
translations. Grey Havens grants no license to copy, distribute, modify or otherwise use
any of this material for any other purpose, and grants no rights in its trademarks.

### Contributor terms

By submitting a pull request, issue, comment or any other material to this repository
(a "Contribution"), you agree to the following:

1. **License to Grey Havens.** You grant Grey Havens, and its successors and assigns, a
   perpetual, worldwide, non-exclusive, royalty-free, fully paid-up, irrevocable license,
   with the right to sublicense and transfer, to use, reproduce, modify, adapt, translate,
   create derivative works of, publicly display, publicly perform, distribute and
   otherwise exploit your Contribution, in whole or in part, in any media and for any
   purpose, including in Spiral Knights and its marketing and promotion.
2. **No compensation.** You will not receive any payment, royalty or other compensation
   for your Contribution.
3. **No obligation.** Grey Havens has no obligation to use your Contribution, to credit
   you, or to keep your Contribution in the game, and may edit or remove it at any time.
4. **Moral rights.** To the extent permitted by law, you waive, and agree not to assert
   against Grey Havens or its licensees, any moral rights or similar rights you have in
   your Contribution, including any right to be identified as its author or to object to
   changes to it.
5. **Your promises.** You represent that:
   - your Contribution is your own original work, or you otherwise have the right to
     grant the license above;
   - your Contribution does not include material copied from any other game, product or
     third party, and does not infringe or violate anyone's copyright, trademark, privacy
     or other rights;
   - if your employer or anyone else has rights to work you create, you have their
     permission to make the Contribution; and
   - you are of legal age to agree to these terms, or your parent or legal guardian has
     read and agreed to them on your behalf.
6. **No warranty.** You provide your Contribution "as is", without warranty of any kind,
   and you are not responsible for supporting it.

If you do not agree to these terms, do not submit a Contribution.

## Ancient history

We used to have a google spreadsheet. We could push a button and it would export the current
english translations and also import anything from any of the corresponding columns for
each language. Perhaps it would be nice to re-create something like that, built on top of this.

Having a front-end for nicely typing-in a label or message and having it automatically output
a well-formatted .properties file would be great!
