Releasing Ambassador
====================

If you just want to **use** Ambassador, check out https://www.getambassador.io/! You don't need to build - much less release! - anything, and in fact you shouldn't.

If you don't work at Datawire, this document is probably not going to help you. Maybe check out [the developer guide](BUILDING.md) instead.

----

If you're still reading, you must be at Datawire. Congrats, you picked a fine place to work! To release Ambassador, you'll need credentials for our Github repos.

1. PRs will pile up on `master`. **Don't accept PRs for which CI doesn't show passing tests.**

2. Once `master` has all the release drivers, tag `master` with an RC tag, e.g. `v0.77.0-rc1`. **This version tag must start with a 'v'.**

3. The RC tag will trigger CI to run a new build and new tests. It had better pass: if not, figure out why.

4. The RC build will be available as e.g. `quay.io/datawire/ambassador:0.77.0-rc1` and also as e.g. `quay.io/datawire/ambassador:0.77.0-rc-latest`. Any other testing you want to do against this image, rock on.

5. When you're happy that the RC is ready for GA, **first** assemble the list of changes that you'll put into CHANGELOG.md:
   - We always call out things contributed by the community, including who committed it
     - you can mention the contributor with a link back to their GitHub page
   - We always call out features and major bugfixes
   - We always include links to GitHub issues where we can
   - We rarely include fixes to the tests, build infrastructure, etc.

6. Once the change list is assembled, hand it to Marketing so they can either write a blog post or tell you it's not needed.

6. While the blog post is being written, sync up the docs!
   - `make pull-docs` to pull updates from the docs repo
   - Handle conflicts as needed.
   - Commit any conflict-resolution changes to `master`.

7. After the docs are synced, use `make release-prep` to update `CHANGELOG.md` and `docs/versions.yml`.
   - It will _commit_, but not _push_, the updated files. Make sure the diffs it shows you look correct!
   - Do a manual `git push` to update the world with your new files.
   - It is *critical* to update `docs/versions.yml` so that everyone gets the new version.

8. Now for the time-critical bit.
   - Tag `master` with a GA tag like `v0.77.0` and let CI do its thing. **This version tag must start with a 'v'.**
   - CI will retag the latest RC image as the GA image.

9. _After the CI run finishes_:
   - `make push-docs` _after the retag_ to push new docs out to the website.
   - Go to https://github.com/datawire/ambassador/releases and create a new release.
      - `make release-prep` should've output the text to paste into the release description.

   **Note** that there must be at least one RC build before a GA, since the GA tag **does not** rebuild the docker images -- it retags the ones built by the RC build. This is intentional, to allow for testing to happen on the actual artifacts that will be released.

   **Note also** that even though the version _tag_ starts with a 'v', the version _number_ displayed by the diag UI will _not_ start with a 'v'.**

10. Submit a PR into the `helm/charts` repo to update things in `stable/ambassador`:
   - in `Chart.yaml`, update `appVersion` with the new Ambassador version, and bump `version`.
   - in `README.md`, update the default value of `image.tag`.
   - in `values.yaml`, update `tag`.
   - Helpful stuff for this:
      - git checkout master               # switch to master
      - git fetch --all --prune           # make sure our view of remotes is up to date
      - git pull                          # pull down any changes to master
      - git rebase upstream/master        # move master on top of upstream
      - git push                          # push rebases to our fork
      - git checkout -b update/$VERSION   # switch to a feature branch
      - make your edits
      - git commit -a                     # commit changes -- don't forget DCO in the message!
      - git push origin update/$VERSION   # push to feature branch
      - open a PR
    - Once your PR is merged, _delete the feature branch without merging it back to origin/master_.

11. Update the getambassador.io website by submitting a PR to the `datawire/getambassador.io` repo.
   - `src/releaseInfo.js` is the only file you should need to touch:
      - `ReleaseType` comes from Marketing, usually "Feature Release", "Maintenance Release", or "Security Update"
      - `CurrentVersion` is e.g. "0.78.0" -- no leading 'v' here
      - `BlogLink` is the full URL of the blog post (from Marketing), or "" if there is no blog post
   - Make your edits, submit a PR, get it merged. Done.
      - If you want to test before submitting, use `npm install && npm start` and point a web browser to `localhost:8000`

   Submit a PR to the Ambassador website repository to update the version on the homepage.
