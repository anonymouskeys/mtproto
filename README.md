# MTProto

Automatically updated MTProto proxy list for Telegram, refreshed every 4 hours.

## Subscription

After the first successful workflow run, open `proxies.txt` and select **Raw**.
For a repository using `main`:

```text
https://raw.githubusercontent.com/anonymouskeys/mtproto/main/proxies.txt
```

The UTF-8 file contains one `tg://proxy?server=...&port=...&secret=...` link per line.
Paste its URL into an application that explicitly supports MTProto list subscriptions.
Telegram supports opening individual proxy links; this TXT endpoint does not itself
make Telegram automatically import or refresh a subscription.

## Updates

GitHub Actions collects lists at 00:17, 04:17, 08:17, 12:17, 16:17 and 20:17 UTC.
The workflow also supports **Actions → Update MTProto proxies → Run workflow**.
GitHub may delay or drop scheduled runs during high load. Public repository schedules
can be disabled after 60 days without repository activity.

The collector normalizes links, removes duplicate endpoints with identical secrets,
and sorts the output. It checks link structure, not proxy reachability or MTProto
handshakes. Public proxies may be offline or unavailable in your region.

If some sources fail or yield no accepted links, only the successful sources are
published and a generic warning is logged. If all sources fail or no links are
collected, the previous file remains unchanged and the run fails. Unchanged lists
produce no commit. A timeout fails the run without publishing a partial write.

## Private configuration

Create an Actions repository secret named `PROXY_SOURCES` containing HTTPS source
URLs, one per line. Both GitHub file-view and raw URLs are accepted. Duplicate
source URLs are normalized. Source lists must contain plain-text proxy links.

Sources are supplied only to the collection step. They are not embedded in this
repository, the resulting TXT, or collector error messages. This hides the configured
source list from ordinary repository visitors; it cannot prevent matching public
proxy entries to upstream lists. Trusted maintainers who can change workflows may
extract secrets. Do not commit private configuration or turn on shell tracing.

Optional Actions repository variables:

| Variable | Purpose |
| --- | --- |
| `COMMIT_NAME` | Author name for automatic commits |
| `COMMIT_EMAIL` | Author email, preferably your GitHub-provided noreply email |

Without these variables, commits use `github-actions[bot]`. With your own linked
email, commits in the default branch of your standalone repository can count toward
your profile contributions. Actual list changes are required; no empty commits are
created. Contribution display can take time to update.

The workflow requests `contents: write`. Repository or organization policies and
branch protection can still prevent pushes; inspect Actions errors if publishing
fails. Only scheduled and manual events are enabled; pull requests cannot run this
workflow with secrets.

## Local check

Python 3.12, standard library only:

```sh
python -m unittest discover -s tests -v
```

For a local collection run, supply `PROXY_SOURCES` via the environment and run
`python scripts/collect.py`. Avoid placing secret values in shell history.

## Documentation

- [GitHub Actions schedules](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
- [GitHub contribution criteria](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference)
- [Telegram proxy links](https://core.telegram.org/api/links#mtproto-proxy-links)
