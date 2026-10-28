# OLA

Open League Analyzer rates how well a player performed in League of Legends ranked solo/duo games compared with other players in the same role.

## Players

**Riot ID**:
The name a player is looked up by, written `gameName#tagLine`. The player can change it, and Riot takes some time to resolve a new one.
_Avoid_: Nickname, summoner name, username

**PUUID**:
The permanent identifier of a Riot account; it never changes, even when the Riot ID does.
_Avoid_: Account ID, summoner ID, player ID

**Searched player**:
The player whose Riot ID was looked up and whose profile is being shown; every other participant in their games is just a participant.
_Avoid_: Caller, user, me

**Ranked entry**:
A player's ranked solo/duo standing: tier, division, LP, wins and losses.
_Avoid_: Metadata, rank data, league data

## Scoring

**Performance score**:
The 0–100 number shown for a player in one game: the percentile of their raw score among players of the same role in the reference.
_Avoid_: Rating, percentile (unqualified), grade

**Raw score**:
The weighted sum of a player's role-standardised features in one game, before it is placed in the reference distribution.
_Avoid_: Score (unqualified), z-score

## Riot routing

**Platform**:
The Riot server a League account lives on, named by its platform routing value. Its short label is only a display name for it:

| Label | Platform |
| ----- | -------- |
| BR    | br1      |
| EUNE  | eun1     |
| EUW   | euw1     |
| JP    | jp1      |
| KR    | kr       |
| LAN   | la1      |
| LAS   | la2      |
| NA    | na1      |
| OCE   | oc1      |
| TR    | tr1      |
| RU    | ru       |

_Avoid_: Region, server

**Regional routing value**:
The cluster of platforms that shares account and match data; each platform belongs to exactly one.

| Regional routing value | Platforms           |
| ---------------------- | ------------------- |
| americas               | BR, LAN, LAS, NA    |
| asia                   | JP, KR              |
| europe                 | EUNE, EUW, RU, TR   |
| sea                    | OCE                 |

_Avoid_: Region (unqualified), continent
