# WocaFuckOff

![logo](assets/logo.png)

**Project Overview**

- **Purpose:** Automated helper for Wocabee language practice using a browser CDP connection.
- **Main script:** [startup.py](startup.py) ! The script doesn't have a gui, if you want I made a [docker image](https://github.com/toomcis/WocaFuckOff-docker) for this project !
- **Main Solver script** [solver.py](solver.py)
- **Primary language focus:** Slovak (designed for Slovak → English), but the approach is language-agnostic in principle.

**Quick Notes**

- **AI-assisted:** This project was created with AI help and may contain bugs or imperfect heuristics. Don't be scared of making an [issue](https://github.com/toomcis/WocaFuckOff/issues) and reposting any bugs or imperfections!
- **Playwright-powered:** Uses Playwright with an installed Chromium build inside the container.
- **Notification support:** Optional integration with ntfy for runtime and startup error notifications.

---

## Requirements

- **WocaBee:** Please make sure that you have a valid WocaBee account and the package already completed before you farm it, the script is supposed to do the tedious grind currently
- **Python:** 3.9+ recommended
- **Libraries:** See `requirements.txt` (if present). At minimum the script uses `playwright`, `requests`, `toml`.
- **Playwright:** Please use the `playwright install-deps` and `playwright install` command to fully install all additional dependencies

---

## Usage

- There are 2 ways to use the script, you can either use the script or the [docker](https://github.com/toomcis/WocaFuckOff-docker)

## Docker

- Follow the instructions on the [WocaFuckOff-docker](https://github.com/toomcis/WocaFuckOff-docker) repository page

## Local

- Before you start the script you need to download the dependencies using these commands
```bash
# Installing requirements and dependencies
python -m pip install -r requirements.txt
python -m playwright install-deps
python -m playwright install
```
- You need to use a chromium based browser, doing the before mentioned `playwright install-deps` should download one that works ! NOTE: Please don't use your own chromium based browser, It has not beed tested properly !
- The startup script will automatically open the chromium browser with the correct arguments
- Running the bot:
- While using the startup.py script, you need to insert username and password into the [config.toml](config.example.toml) file

```bash
# You rely on config.toml for all variables
python startup.py
```

---

## Configuration

- Create and edit a config.toml file (You can use the [config.example.toml](config.example.toml) file as a base). All variables are:
    
| Variable             | Default                   | Description                      | Optionable                                            |
| -------------------- | ------------------------- | -------------------------------- |-------------------------------------------------------|
| `urlbase`            | `https://wocabee.app/app` | Target Wocabee URL               | ✅ ! Dont change unless you know what you are doing ! |
| `debug_port`         | `https://localhost:9222`  | CDP endpoint                     | ✅ ! Dont change unless you know what you are doing ! |
| `wordlist_file`      | `wordlist.json`           | JSON file storing word mappings  | ✅ ! Dont change unless you know what you are doing ! |
| `picture_file`       | `picturelist.json`        | JSON file storing image mappings | ✅ ! Dont change unless you know what you are doing ! |
| `placeholder_words`  | `translate,check`         | Words to ignore                  | ✅ ! Dont change unless you know what you are doing ! |
| `username`           | (empty)                   | Login username                   | ❎                                                    |
| `password`           | (empty)                   | Login password                   | ❎                                                    |
| `double_points`      | `false`                   | Enable double points mode        | ✅                                                    |
| `addon_points`       | `5000`                    | Target addon points              | ✅                                                    |
| `milestone_reminder` | `1000`                    | Reminder interval                | ✅                                                    |
| `headless`           | `false`                   | Enable headless browser mode     | ✅                                                    |
| `class_index`        | `0`                       | Class selection index            | ✅                                                    |
| `package_index`      | `0`                       | Package selection index          | ✅                                                    |
| `ntfy_server`        | (empty)                   | ntfy server URL                  | ✅                                                    |
| `ntfy_topic`         | (empty)                   | ntfy topic                       | ✅                                                    |
| `ntfy_token`         | (empty)                   | ntfy auth token                  | ✅                                                    |

### Example config snippet (see the example [config.toml](config.example.toml) for the full file):

```toml
urlbase = "https://wocabee.app/app"
debug_port = "http://localhost:9222"
wordlist_file = "wordlist.json"
picture_file = "picturelist.json"
placeholder_words = ["", "translate", "check"]
class_index = 0
package_index = 0
addon_points = 1000
milestone_reminder = 100
headless = true
double_points = false
username = "coolUsername"
password = "coolPassword"
ntfy_server = "https://example.ntfy.server"
ntfy_topic = "wocabee-bot"
ntfy_token = "secret_token_here"
```

---

## How it works (short)

- The startup.py script opens a chromium browser with specific arguments and automatically navigates to a specific class and package you want to farm
- The solver.py script automatically starts and attaches to the browser via CDP, finds the website, and automates UI actions with Playwright.
- Mappings for words and pictures are stored in JSON files (`wordlist.json`, `picturelist.json`). Unknown items may prompt for manual input once and get saved. ! NOTE: If you get specific new words, please map them and send them into an [issue](https://github.com/toomcis/WocaFuckOff/issues) under the tags `additional word mapping` or `additional picture mapping`

### Limitations & Caveats

- The project was generated/assisted by AI — expect brittle behavior and imperfect code, if any issue arises please report it in the [issues](https://github.com/toomcis/WocaFuckOff/issues).
- It assumes specific DOM IDs and classes on the target site; UI changes will break handlers.
- Designed and tested against Slovak-English examples; other languages may require adjusting the translation fallback settings and the `source` language in the translator calls.
- Use responsibly: automated interaction with websites may violate terms of service. I am not responsible for any bans that might come with breaking ToS of the WocaBee app.

### Troubleshooting

- If handlers fail to click elements, the site DOM may have changed; open [solver.py](solver.py) and inspect the locator logic.
- Network/translation failures fallback to manual prompts — check `wordlist.json` and `picturelist.json` for saved entries.

---

## License & Attribution

- This project uses the [MIT license](LICENSE)
