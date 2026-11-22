# Clubhouse changelog

## 1.13.1 (November 22, 2026)

- **More gear pictures:** 343 of the 409 branded items now have a picture, up from 317, including more legend bats (Buck O'Neil, Hilton Smith, Martin Dihigo, Rube Foster, Ernie Banks, Jimmie Foxx) and the Chandler JAZZ.X. The extra pictures come from The Show's MLB 25 and MLB 24 item databases. Items with no picture anywhere still show a slot icon.

## 1.13.0 (November 22, 2026)

Road to the Show comes to Clubhouse, with gear challenges, packs and a locker that equips real branded gear on your player, even offline.

### Two modes
- A **Franchise | Road to the Show** switch in the top bar. It appears when Clubhouse finds a Road to the Show career in your save folder.
- **Road to the Show mode** shows only your player: Home, Stats, Challenges, Inventory and Locker, in your organization's colours. Franchise mode is unchanged.
- Clubhouse picks up new career saves by itself, a few seconds after you save in the game.

### Your player
- **Home:** your club, level, position, overall, this set's challenges, packs to open, equipped gear and this season's stats.
- **Stats:** hitting and pitching by level (AA, AAA, MLB) plus your ratings. Two-way players get both.

### Challenges
- Every **20 of your games** (games you hit in plus games you pitched in) you get three challenges at each difficulty. Pick one easy, one medium and one hard.
- Targets come from your own pace. Some are counting stats (hits, home runs, RBIs, strikeouts, wins, innings), others are rate stats (hit .350 over 50+ at-bats, an ERA under 2.00).
- Finish one before the 20 games run out to earn a pack: easy gives **Silver**, medium **Gold**, hard **Diamond**. Then a new set starts.
- Stats count at every level, and call-ups don't reset anything. Simmed games count too.

### Packs and the locker
- Every career starts with **3 Silver, 2 Gold and 1 Diamond** pack.
- **Inventory:** open a pack and a reel spins through that rarity's gear and lands on your item. You get something new until you own every item of that rarity.
- **Locker:** your gear as big picture cards. Click one to see it full size and **Equip** it.
- **13 gear slots:** bat, batting gloves, fielding glove, cleats, elbow guard, bat grip, glasses, compression sleeve, wrist guard, leg guard, catcher's mask, catcher's shin guards and chest protector.
- About 440 items from the game's own catalog, including legend signature bats, with pictures and rarity from The Show's item database.
- **Unlock all gear** (in the Locker): equip anything without challenges.

### How to use it
1. Restart Clubhouse after updating, then click **Road to the Show** in the top bar.
2. Open **Challenges** and pick one easy, one medium and one hard.
3. Play or sim, then save in the game. Clubhouse updates your progress by itself.
4. Open your packs in **Inventory**.
5. To equip gear: **close the game and the emulator**, open the **Locker**, click an item and press **Equip**. Then load your career in the game.

Equipping changes only that one slot in your career save. Clubhouse backs up the save first, then reads it back to check. If you pick a different item for that slot in the game's Edit Player screen, the game replaces it, and you can equip it again from the Locker. Colours stay with the game's Edit Player menus.

## 1.12.1 (November 21, 2026)

- **Fixed:** after updating, Clubhouse could keep showing the previous version's pages, so the Salary cap and Draft lottery from 1.12.0 didn't appear. Clubhouse now clears its page cache on every start. Your settings, boards and cap records are kept.

## 1.12.0 (November 21, 2026)

A salary cap and floor for your franchise, with real draft-pick penalties written into the game, plus a draft lottery for 2027 rosters. Everything here is optional and off until you use it. New and still being tested: **keep a copy of your franchise save before using any "in-game" button.**

### What's new

- **Salary cap (Front office → Salary cap).** Every club's payroll against a $245.3M cap and a $171.2M floor, both growing 3% a season. Payroll counts every major-league contract in the organization at its yearly average.
  - **League:** all 30 clubs, cap room, status and the game's budget for each club.
  - **Club pages:** the contracts counted, the next three seasons of commitments and flags for very long or very large deals.
  - **Rules:** the cap, floor, growth, rounds forfeited, when penalties start and more. Saved on your PC for every franchise.
- **Draft penalties, in the game itself.** A club over the cap on **Opening Day** loses its **Round 1 and Round 2** picks in that summer's draft. The picks are removed from the game's draft order, and every club behind them moves up.
  - No penalties in a franchise's first season. They start in the second.
  - Penalized clubs also lose their compensation and prospect promotion picks.
  - Competitive Balance rounds A and B are created by the game and can't be changed.
- **Draft lottery for 2027 rosters (Draft → Draft lottery).** It follows MLB's lottery rules and the real 2026 standings.
  - The 18 non-playoff clubs draw for picks 1–6, revealed one at a time.
  - Picks 7–18 go in reverse record. Playoff clubs pick 19–30, by how far they went.
  - You can draw again until you write the result to your save. From the second season on, the game runs its own lottery.
- **Make the AI respect the cap (optional).** Lowers every AI club's budget that's above the cap down to the cap, so they stop adding payroll. Clubs under the cap keep their budgets, and yours is never touched.
  - Choose "Ask me" or "Apply automatically" each new season (Rules → AI budgets each new season).
  - **Restore original budgets** undoes it and turns automatic mode off.
  - Untested so far: we don't yet know how strictly the AI follows its budget.

### How to use it, step by step

**Before you start**
1. Restart Clubhouse after updating.
2. Pick your franchise from the franchise menu in the top bar.
3. Optional: set your cap, floor and penalty rules on Salary cap → Rules. If you want AI budgets capped, choose "Apply the cap automatically" there.

**First season (2027 rosters): set up the draft**
1. In spring or on Opening Day, open Draft → Draft lottery and press **Run the lottery**.
2. Close the game, then press **Write this order to my save**.
3. Sim on. Your lottery order is what the game drafts from in July.

**Every Opening Day, from the second season on**
1. Sim to Opening Day and save.
2. Close the game (and the emulator), then open Clubhouse. It records every club's payroll for the Opening Day check from the first save it sees on or after Opening Day. Don't skip ahead to May, or May payrolls will be used.
3. Open Salary cap → Draft penalties. It lists the clubs over the cap and shows the original and adjusted draft orders side by side.
4. Press **Apply penalties in-game**. Your save is backed up first.
5. Sim to the draft and check that Rounds 1 and 2 match the adjusted order.

**Each new season, if you use AI budgets**
1. The game rebuilds every club's budget each season. After the season changes, open Clubhouse once with the game closed.
2. With "Apply automatically" on, Clubhouse applies the cap by itself and tells you. With "Ask me" on, a banner asks you.
3. Do this before you sim far into free agency.

**Changing your mind**
- **Restore the original draft order** (Draft penalties tab) puts the game's order back exactly.
- **Restore original budgets** puts that season's budgets back.
- Both need the game closed and work any time before that season's draft.

### Safety

- Every write refuses while the game or an emulator is running. It backs up your save to Clubhouse's settings folder first, then reads the save back to check that only the intended bytes changed.
- Draft order writes can only remove picks or reorder clubs within a round. They never give a club a pick it didn't have.
- Writes refuse once that season's draft has started.

### Fixes

- Cap and penalty records are now kept in a file, so they survive restarts and can't be lost or re-taken from a later save.
- Clubhouse waits for its usual window port after a restart instead of opening with empty page storage.

## 1.11.0 (November 21, 2026)

- **2027 roster support.** Clubhouse spots franchises started on rosters that already include the real 2026 season, and treats them as the 2027 season even though the game's calendar says 2026. Seasons, free agency, the draft class, awards and history all use 2027, and the years keep counting up as your franchise advances. Dates and weekdays still follow the game.
- **Player cards keep real history.** Real seasons keep their real years, the 2026 season counts as last season, and last year's rookies are no longer treated as rookies.
- Normal franchises are unchanged.

## 1.10.0 (November 21, 2026)

- **Discover in game.** Prospects your Clubhouse scouts found but the game hasn't are now marked "Hidden in game". One click puts them on the game's draft list (as NR), from Scouting → Discoveries or the prospect's profile.
- Only that one value changes in your save, and only after you confirm. The game must be closed. Clubhouse backs up your save first and checks it afterward.

## 1.9.0 (November 21, 2026)

### Assistant GM
- **A new Assistant GM page** (Front office → Assistant GM), with your club's real assistant GM as the persona. If your club's assistant GM has changed, you can change the name, title and photo; it's saved on your PC.
- **Briefing:** what you might miss.
  - Roster: injuries with the next man up, slumping regulars, minor leaguers who are ready, your weakest spot, a taxed bullpen and struggling starters.
  - Contracts: expiring deals with projected price tags, and arbitration costs with tender advice.
  - Calendar and the rest: the trade deadline, call-ups, the playoff race, hitting streaks and home-run pace, the draft, payroll and scouting.
  - The top items also show on Home.
- **Ask him anything** about the roster, trades ("Should I trade X for Y?", "What can I get for X?", "What would X cost?"), contracts and arbitration, free agents, needs, the lineup, rotation and bullpen, call-ups, prospects, the playoff picture, injuries or payroll, or compare two players. He answers from your save, offline, and never reveals hidden prospect ratings.

### Playoffs
- **A Playoffs header** appears in September and stays through the end of the season.
- **Bracket:** the projected (or final) bracket for both leagues, with pennant and World Series odds from 800 simulations of the rest of your real schedule.
- **Your road:** a plan for every round you're likely to play, with your playoff rotation, high-leverage arms, edges for both sides, series odds and a link to the full game plan. If you're outside the field, it shows the chase instead, with a tragic number.
- **Playoff wire:** clinches, eliminations, division and wild card races, hot and slumping contenders, injuries, aces lining up and wild card previews.
- **Odds:** playoff, division, bye, pennant and World Series odds for all 30 teams, plus mathematical clinch and elimination.

### Match report
- **Fairer win chances.** Records are discounted toward .500 (heavily early in the season), and a single game stays between 30% and 70%. Each game shows what drove the number.
- **Edges for both teams, measured the same way.** About 20 kinds are checked, including how a team hits the hands it will actually face this series, short rest, hitting with runners in scoring position, running on a weak-armed catcher, walks against a wild staff, a tired closer, the season series, home and road records, injuries and double-play chances against sinkerballers.
- **A scouting report for each team** (identity, threats, platoon, approach, rotation, bullpen, defense, form, injuries) and a series preview.
- **Pitching tips built from each hitter's profile and your starter's real pitches**, written in many different ways rather than "pitch away" every time.
- **New: an at-bat plan for each of your hitters** against their starter, a bullpen plan matching your relievers to their best hitters, and how to attack their bullpen.

### The real postseason
- **Clubhouse reads the postseason from your save:** every series, game scores and winning and losing pitchers. In October the Playoffs pages follow the real bracket instead of a projection.
- **Your game plan is always against your actual opponent.** If your likely opponent loses in the Wild Card round, the plan switches to the team that beat them, with the series score and game numbers.
- **Your road:** your current series, results so far and the likely next opponents from the live bracket. Plus a recap of your October, and a season-over or champions page when it's done.
- **Bracket and odds:** the real bracket with series scores, and pennant and World Series odds simulated from the current series scores.
- **Playoff wire:** real results, series scores and previews of the next series.
- **Fixed: stats during the postseason.** The game swaps season stats for playoff stats in October. Clubhouse now rebuilds each player's regular season, so leaders, reports and edges keep working, and keeps playoff stats separately.

### Fog of war on potential
- **Every player's and prospect's potential is now an estimated range** instead of an exact number: tables, player cards, prospect lists, spring camp, the assistant GM and the match report. Ranges are wider for young players and tighter for veterans and your own organization, and they always contain the true value. Draft prospects stay hidden.

### Fixes
- Rookie of the Year only counts real MLB rookies (career at-bats, innings and service time), so veterans like Shohei Ohtani are out.
- The season series between two teams reads the same on every page.

## 1.8.2 (November 21, 2026)

### Fixed: updates didn't install
- **Restarting after an update reopened the old version.** The installer couldn't replace the Clubhouse folder while Windows considered it "in use", and that included its own working folder.
- It now runs from outside the Clubhouse folder. If the folder still can't be swapped (for example, it's open in File Explorer), it copies the new files in place instead, after backing up the old ones.
- **Install this version by hand once.** 1.8.0 and 1.8.1 have the old installer, so they can't install updates themselves. From 1.8.2 on, updates install from the banner.

## 1.8.1 (November 21, 2026)

### New Clubhouse logo
- The new Clubhouse emblem replaces the old baseball mark everywhere: the app and window icon, the top bar, the welcome screen and the loading screen.

## 1.8.0 (November 21, 2026)

### Updates inside the app
- **Clubhouse now updates itself.** It checks for a new version when it starts and every few hours. When one is out, a banner shows it, with **What's new** (the release notes), **Update now** and **Later**.
- **Update now** downloads in the background with a progress bar and checks the download against its published SHA-256 before using it. **Restart to update** swaps in the new version and reopens Clubhouse.
- **Nothing of yours is touched:** your saves, settings, scouting department and franchise history stay put. The previous version is kept next to the new one as a backup (`Clubhouse.old`).
- **Settings → Updates:** check now, or turn automatic checks off. "Skip this version" hides one release.
- This is the last version you need to install by hand; later versions arrive through the app.

## 1.7.1 (November 20, 2026)

### Spring training fixes
- **Fixed: saves from later in spring said "Spring training is over."** Clubhouse now reads the game's own spring flag, so it recognizes spring on any day of camp. It also reads the date correctly: the game counts spring days from the start of camp.
- **Spring stats now work.** The game keeps spring games in the current-season stats, and the Spring training page uses them for the stats tab, standouts and struggles, and a small nudge to the 26-man projection.
- **Spring is labeled as spring across the app.** The top bar, ticker, power rankings, leaders, standings and the wire show "spring" or "spring day".
- **The series plan and Home spotlight show the Opening Day series** instead of a series deep into the regular season.
- **Upcoming spring games have the right dates.**
- **No press conferences after spring games.** The press room starts fresh at Opening Day, even if an earlier version counted spring games.
- **Spring saves aren't recorded in franchise history or the between-save stat changes,** and entries an earlier version recorded from spring are replaced when the season starts.

## 1.7.0 (November 20, 2026)

### Spring training
- **New Spring training page** (My team → Spring training). While a save is from spring, Home shows a "Camp is open" banner linking to it. Clubhouse reads the save's own spring calendar, so it knows the camp day and how many days are left to Opening Day.
- **Overview:**
  - Your 40 players in camp and a projected 26-man Opening Day roster: lineup, bench, rotation and bullpen.
  - Each player gets a status: Lock, Likely, Bubble, Starts in the minors or Opens on the IL.
  - It warns about roster gaps, such as no backup catcher, and suggests who could fill them.
- **Position battles:** every job within a few points, including minor leaguers who could take one. It compares the players' ratings and last season's lines, spots platoon fits and upside, and says what to watch in each battle.
- **Who needs a look:** bubble players, young players who might be ready, last season's overperformers and bounce-back candidates, platoon questions, injuries, rotation depth and your top prospects. Each one says what to look for this spring.
- **Not on the 40-man:** minor leaguers who could win a job or push for one, measured against the 26-man cut line, with ETA and org rank. It also lists who could lose a 40-man spot if you need room.
- **Playing time:** a suggested spring workload for every player in camp. Battles and bubble players get the most at-bats and innings, while locks just get ready.
- **Spring stats:** your camp's spring numbers, with standouts and players struggling against their ratings. Spring results move the projection only slightly.
- Fixed a crash closing the press room when no league had loaded.

## 1.6.0 (November 20, 2026)

### International scouting
- **New "International prospects" specialty.** Every International scout now has it as his main specialty, including scouts already on your staff or in the hiring pool.
- **International prospects are harder to read.** These are players in the Latin America & PR territory. Scouts with no international background are about 12% less precise on them. International specialists, and any scout whose territory is Latin America & PR, avoid the penalty, and the specialists are sharper still.
- **The hiring pool always has at least 2 international specialists.** International scouts also show up more often in general, and area scouts can now be based in Latin America & PR.
- **The assignment dialog** warns you when nobody on your staff has international experience and links straight to international scouts in the hiring pool. Each scout is tagged "International background" or "No international experience".
- "How scouting works" explains all of this.

## 1.5.0 (November 20, 2026)

### Player headshots
- **Real MLB headshots for about 2,200 players**, including 803 of the 805 players on MLB rosters in the test save and many minor leaguers. They're bundled with the app, so they work offline.
- **Where they show:**
  - the player card, as a large cutout in front of his jersey number;
  - the Players page, team tables, stat tables and minor-league tables;
  - Home's batting and pitching leaders, the leader boards and the Team page's batting order.
- **Matching:** players are matched by name, with age and position used to tell apart players who share a name. Saves from other people's franchises get pictures for the same players.
- **No picture:** players MLB hasn't photographed (mostly lower minor leaguers), created or modded players, and all draft prospects (they're generated by the game) keep a plain silhouette.

## 1.4.0 (November 20, 2026)

### Scout discoveries
- **Every scout has a Discovery rating.** Each week any scout might bring you a player who isn't on the public board. A higher rating means better odds, never a guarantee. A low rating makes finds rarer, never impossible.
  - Weekly chance of a find: about 8% at discovery 30, 14% at 50, 21% at 70 and 29% at 90.
  - At most 2 discoveries a week across the whole department.
  - Scouts mostly find players in their own territory.
- **Some finds are real hidden gems and some are false alarms.** Better scouts are right more often (about half the time at 30, about 85% at 90). The scout's pitch and his gut read of the ceiling never tell you which it is; you have to scout the player to confirm.
- **New Discoveries tab** (with a count of new finds): each find shows the scout's pitch, his gut read and, once you've scouted the player, your department's current read. It has one-click "Scout to confirm" (it sends the scout who found him when he has room), Watchlist and Dismiss. Filters: Waiting on you, Real finds, Everything, Dismissed. A "Who finds players" table shows each scout's discovery rating and track record.
- This week's page shows new discoveries, and scout profiles, the hiring pool and scout comparisons all show Discovery. Scouts with strong discovery cost a little more.

### Cleaner scouting pages
- Tabs, filters and buttons are rounded pills with smooth hover and focus effects.
- The Find players status filter is now a row of chips with counts, and there are new All positions / Hitters / Pitchers chips.
- Cards and panels have softer corners and lift slightly on hover.

## 1.3.0 (November 20, 2026)

### Scouting is easier to use
- **"How scouting works" tab:** the whole system in plain language, with the real numbers. It covers the three steps, how much you can scout each week, every assignment type and what it costs, how to read ranges and confidence, why stats can lie, how scouts and money work, and good habits.
- **Your capacity this week:** the department page now says exactly how many first looks or shorter assignments you can still start this week, and whether scouting points or your scouts' time is the limit. Each scout shows his free work units and what he can still take. The assignment dialog shows the same summary.
- **Reports grouped by player:** each player gets one block with his current read and all his reports in order, with unread ones marked. You can filter to only new reports or mark everything as read. The department page shows the latest players with their three newest reports.
- **A 3-step guide** at the top of the department page highlights where you are: pick players, keep playing, read and repeat.
- **Bigger, easier-to-read text** on every scouting page and in the assignment dialog.
- **Clearer names:** This week, Find players, Reports, Watchlist, My scouts, Hire scouts. Profile and report pages have back links, and the player list's buttons now read Scout and Choose.

## 1.2.0 (November 20, 2026)

### Scouting
- **Attributes tab:** each prospect has a rough sketch of every rating once your scouts have seen him: contact and power by hand, vision, discipline, glove, arm, speed, stamina, each pitch's velocity and movement, and more. Each rating shows as a range with its confidence. Areas you haven't scouted stay blank.
- **Amateur stats:** every prospect has a spring stat line and a recent stretch (last 10 games, or last few starts or outings), built from his real ratings plus luck.
  - Most weak players put up weak numbers.
  - Some average players have hot seasons, a few weak players have hot streaks, and some good players slump.
  - Less experienced scouts can be fooled by the numbers. Good scouts tell you when the stats don't match the tools.
  - The numbers are labeled as Clubhouse's invention, not the game's.
- **Reports that explain themselves:** every report lists his strengths and weaknesses with the reasons behind them.
  - The more you've scouted him, the more each one includes: what the numbers say and, for weaknesses, what he needs to improve.
  - Each prospect also has a running scouting summary that grows from a first look into a full workup, including risk factors.
- **Weeks start on Sunday.** Weeks are now labeled by date ("Week of Aug 2"). Existing scouting data converts automatically.
- **Easier to use:**
  - Each prospect shows a recommended next step with a one-click Scout button that sends your best available scout. You can still choose the scout and assignment yourself.
  - Prospect pages are split into Summary, Attributes, Stats, Reports and History.
  - The department page opens on "This week": new reports to read, SP you're about to lose, idle scouts, and who to scout next.
  - The prospect list shows his stats, what you know and the next step at a glance.
  - Unread reports are marked "New".

## 1.1.0 (November 20, 2026)

### New: Scouting department

Run your own amateur scouting operation instead of the game's scouting bar. Your scouts look at the real prospects in your save, but they only ever report what they think they saw: ranges and confidence, never exact ratings.

- **Scout pool:** about two dozen scouts available to hire at any time, each with ratings, specialties, a home territory, a scouting philosophy and tendencies that actually shape their reads.
  - Each scout is one of 10 types: crosscheckers, area scouts, pitching and hitting evaluators, tools scouts, analytics-minded evaluators, makeup and defense specialists, international scouts and associates.
  - You can filter, sort and compare up to three side by side.
  - The pool turns over every 6 weeks, and fully at the new year.
- **Hiring and money:** your department has $1.8M a year.
  - Scouts sign one-year contracts. You pay the hiring fee and a full year's salary up front, and the salary again each year he stays.
  - An elite crosschecker costs about $430–460K a year plus a 40% hiring fee, so you can afford roughly two.
  - Each scout's profile shows exactly why he costs what he does.
  - You can carry up to 8 scouts. Releasing one refunds the salary for contract weeks he hasn't worked yet, minus 25% severance.
- **Scouting points (SP):** your department earns SP every week. Better and bigger staffs earn more, up to 100. Only 20 unspent points carry over.
- **Assignments:** initial evaluation (12 SP), follow-up (8), hitting, pitching or defensive focus (6 each), makeup and background (5), and live scouting (10).
  - Each scout can only carry so much work at once, and an initial evaluation ties him up for two weeks.
  - Before you confirm, you see the cost, his workload and how precise his read should be.
- **Time:** scouting weeks follow your franchise's calendar. When you load a later save, the weeks in between play out: assignments finish, reports arrive and new SP comes in.
- **What you learn:**
  - Every tool is tracked separately: contact, power, approach, speed, glove, arm and receiving for hitters; velocity, swing and miss, control, command, stamina and secondary stuff for pitchers; plus present ability, ceiling, makeup and durability.
  - Each one moves from Unknown to Preliminary, Evaluated, Refined and High confidence as you scout. Ranges narrow with more looks, but never all the way.
  - Better scouts are more accurate, specialists are sharper in their area, and scouts who know the territory see more.
- **Scouts disagree:** every scout's opinion is kept. The department consensus sits next to each scout's own range, and big disagreements are flagged.
- **Reports:** real scouting reports in each scout's voice: blunt crosscheckers, tools-first scouts, cautious analysts, floor-first and ceiling-first evaluators.
  - Formats include formal reports, crosschecker summaries, field notes, follow-ups that say what changed, live-game observations and background investigations.
  - What a report says is based on the player's actual ratings: platoon splits, chasing, an arm that's strong but erratic, his real pitch names, his frame.
- **Character traits:** makeup and background work can uncover traits like work ethic, coachability, baseball IQ, pressure performance and durability. Each one is labeled as either coming from the game's ratings or from Clubhouse's own trait model.
- **Prospect scouting profiles:** everything you know about a player in one place: ranges, confidence, projection, floor, risk, each scout's opinion, traits, a timeline of how his evaluation changed, and every report.
- **Watchlist:** priorities, favorites and your own notes. Taking someone off the watchlist keeps your notes.
- **Alerts:** big changes in a player's evaluation, scout disagreements, traits found, top-priority players you still know little about, idle or overloaded scouts, SP you're about to lose, and budget warnings.
- **Portraits:** give any prospect a photo from your PC. It's copied into Clubhouse's own folder. Prospects without one get a placeholder.
- **Saved safely:** scouting is saved on your PC, separately from the game. Loading new saves never erases it, and a prospect missing from a save is flagged, never deleted.

### Fixed

- **Things that didn't stick:** your starred draft board, press conference answers and power-ranking arrows were lost every time Clubhouse closed. They now stay.

## 1.0.0 (November 20, 2026)

This is the first release of Clubhouse, a franchise companion for MLB The Show 26 (the Switch version, played through an emulator on a Windows PC). It reads your franchise save and puts the whole league in one app. It never changes your save, and it never goes online.

### Getting started

- **Your save folder:** pick it once, and Clubhouse remembers it. You can choose the profile folder or any single franchise folder.
- **Every franchise in the folder:** Clubhouse finds them all. Switch between them from the season menu in the top bar or the franchise cards on Home.
- **Always the newest save:** Clubhouse follows the newest save of the franchise you're viewing, even when the game writes it into a new slot.
- **New saves:** when you save in the game, a "New save found" banner offers to load it. Turn on Settings → "Load new saves automatically" to skip the prompt.
- **Team theme:** the app takes on your team's colors, and each team's page uses its own colors.

### Home

- **Power rankings** for all 30 clubs, with arrows showing movement since your last save.
- **Series spotlight:** a carousel of your upcoming series, with probable starters and win chances.
- **Clubhouse wire:** league notes built from your save, with League, Team and Prospects tabs.
- **Next game:** first pitch, both starters, your win chance and a Game plan button.
- **Leaders:** batting and pitching leaders, with stat tabs.
- **Around the league ticker:** every club's last result.

### League

- **Standings** by division.
- **Wild card race,** with an "if the season ended today" bracket.
- **Power rankings,** built from record, run differential and the last 10 games.
- **Team grades:** lineup, rotation, bullpen, defense and bench, each graded against the other 29 clubs.

### Stats and awards

- **Leaders:** boards for 12 categories.
- **Stat tables:** sortable batting, pitching and team tables, with league, team and qualified-only filters.
- **Award races:** MVP, Cy Young and Rookie of the Year for both leagues.
- **All-Star ballot:** a projected vote by position, plus the game's date and host city.

### Your team

- **Team page:** record, game log, a best lineup shown on a field, a suggested batting order, full rosters and a grade strip.
- **Series plan,** for your next series or one against any team you pick:
  - your edges and weak spots, and a tale-of-the-tape comparison;
  - starters with their pitches and platoon splits;
  - a lineup for each game that accounts for the opposing pitcher's hand;
  - a scouting line on how to pitch each opposing hitter;
  - which relievers are rested, from the last 7 days of pitch counts.

  You can swap any starter.
- **Press room:** an optional postgame press conference after each new game:
  - questions built from the score, the pitchers who got the decisions, hot hitters, your streak and the standings;
  - four answer styles (Confident, Even-keeled, Credit the group, Keep it short), drawn from large pools so they rarely repeat;
  - a "tomorrow's headline" based on your answers, and a history of past conferences.

### Player cards

Click any player to open a full card in the middle of the screen. The header shows his team colors, an outlined jersey number, height, weight, bats/throws, age, overall and potential, plus his contract status and current form.

The card has these tabs:
- **Overview:** quick info, rating tiles, and this season's stat tiles with his MLB ranks. You can switch the stats to last season.
- **Ratings:** every rating, plus his pitches with velocity, movement and usage.
- **Statistics:** every MLB season of his career (back to 2005) with the team he played for, this season live, this season in AAA and AA, and career totals. It also shows splits against left- and right-handers, this month, the current series, and pitch counts for the last 7 days. Two-way players get both a batting and a pitching table.
- **Abilities:** his special abilities, with the game's own names and descriptions.
- **Media:** made-up press coverage based on his real numbers: hot and cold streaks, slumps, breakouts, contract years, injuries, and more. It's different every time you open it, and it comes with a "media temperature" meter and fan reactions.

Minor leaguers also show their prospect rank, their estimated MLB arrival and their trade value.

### Draft

- **Draft board:** the full class of 540 amateurs, with the game's rank, position, bats/throws, school and bonus ask.
  - Ratings are hidden ("?"), just like the game's scouting.
  - "Scouts" stars come from the game's draft rank.
  - After the draft, a Drafted column shows who went where.
- **My board:** star prospects to build your own board.
- **Prospect watch:** made-up amateur-season headlines about real prospects in your save.
  - Each prospect's hidden ratings shape what kind of story he gets.
  - Lesser prospects can have huge days too, so some headline makers will never pan out.
  - Click a name to open his card.
  - The "My board" tab follows only your starred prospects, with an at-a-glance table and daily updates.
- **Draft class:** once the draft happens, your picks appear here, read straight from the save:
  - pick number, signed or unsigned, and bonus;
  - ratings shown as scouting ranges and potential as a letter grade (A to D). The ranges are tighter for players your scouts watched closely in the game.
  - The whole draft, all rounds, is listed below.
  - Earlier years' classes stay available, showing where those players are now.

### Front office

- **Trade evaluator:**
  - Says whether you should buy, buy selectively, hold or sell, from your playoff odds and win pace.
  - Shows your weakest and strongest positions against the average club.
  - Suggests trades, each with what you give and get, a value balance, and the upsides and downsides.
  - Also lists players to target, players to sell, your prospects marked as keepers or trade chips, and prospects worth asking for.
- **September call-ups:** recommends the arm and the bat to add when rosters expand to 28.
  - It favors help-now players when you're contending and young players worth a look when you're not.
  - A full candidate list is included.
- **Franchise history:** every season Clubhouse has read for this franchise, with your record, finish, run differential, farm records and top draft pick. It's kept on your PC, so it survives after the game overwrites old seasons.

### Minor leagues

- **Your farm system:** your AAA, AA and A clubs, with records, standings position, top bat, top arm and the prospects on each roster.
- **Standings** for the International League, Pacific Coast League, Eastern League, Southern League and Texas League.
- **Leaders and stats** for AAA and AA, with an organization filter.
- **Awards** for each league: MVP, Pitcher of the Year and Top Prospect.
- **Futures Game:** the AL organizations' prospects against the NL's, with every club represented and a projected fan vote for the starting lineups.
- **Top prospects:** the top 100 in baseball and your top 30.
- **MLB ETA:** an estimated arrival for every minor leaguer, based on his rating, his production and who he'd have to replace. Hover over it to see the reasons.
- **Performance watch:** the best minor-league lines since your last save, for your system and around the minors. Save after every game day and you get standout performances game by game.
- **Club pages** for every minor-league team, with roster, stats, ratings and ETAs.

### Free agency

- **Upcoming class:** players heading to free agency after this season.
- **Contracts:** any team's payroll, with each player's arbitration or pre-arbitration status and a next-year estimate.
- **Available now:** the unsigned pool.
- **Offseason:** a placeholder for offer tracking, which needs an offseason save to build.
- **Expected deals:** projected salary and years for each player, based on what veterans in your save are paid.

### Quality of life

- **Design:** a clean dark look with team-colored banners. Ratings are colored by tier: 90+ gold, 80s green, 70s blue, 60s gray, under 60 red.
- **Logos:** real team logos, with compact versions in tight spots.
- **Motion:** pages fade in, cards scale in, bars grow, numbers count up, and buttons respond when pressed. All motion is off if Windows is set to reduce animations.
- **Notices:** small pop-ups confirm when a new save has loaded.
- **Navigation:** sortable tables everywhere, and Esc or clicking outside closes cards and pop-ups.
- **Window size:** Settings has 80% to 125% sizes for small or large screens.
- **Update prompt:** if Clubhouse's files are updated while it's open, it offers a one-click restart.
- **Continuity:** everything is read fresh from the save, so each new season brings new stats, prospects, draft classes, contracts and affiliates automatically. Franchise history never rewinds, even if you load an older save.

### Fixed during testing

- **Draft class:** it said the draft hadn't happened after you'd already signed your picks. It now reads the game's draft results directly.
- **Top prospects:** the list showed "null" instead of rank numbers.
- **Wrong save:** Clubhouse could stay on an older save slot of a franchise and show a 0-0 record.
- **Mets save crash:** Home crashed when the save's next scheduled game was a minor-league game.
- **Series spotlight:** it only looked at the very next game instead of upcoming series.
- **Franchise switching:** switching franchises could briefly show the previous franchise's data.
- **Draft board:** prospect attributes showed exact numbers instead of staying hidden.

### Known limitations

- **Supported saves:** only the Switch version's saves. PlayStation, Xbox and PC saves are stored differently.
- **Single-A:** the game doesn't simulate games below AA, so Single-A clubs show rosters only.
- **Untested periods:** the playoffs, the offseason and the start of a second season haven't been tested with real saves yet.
- **Estimates:** trade value, playoff odds, award races, call-up ETAs, the Futures Game and All-Star votes, press conferences and media are all Clubhouse's estimates or inventions, not the game's.
- **40-man roster:** Clubhouse can't see 40-man roster status yet.
- **History:** franchise history starts the first time Clubhouse reads each season.
- **Updates:** shared copies don't update themselves; get the newest folder from whoever shared it.
