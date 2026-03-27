# acd-ics

I follow Ethereum's All Core Dev calls but got tired of manually adding each one to my calendar from the [github issues](https://github.com/ethereum/pm/issues). So I built a live ICS feed that pulls them automatically.

## Usage

Subscribe to this URL in your calendar app (Apple Calendar, Google Calendar, etc.):

```
https://acd-ics.vercel.app/feed.ics
```

That's it. It includes ACDE, ACDC and ACDT calls with their agenda and meeting links.

## How it works

A Vercel serverless function fetches issues labeled `ACD` from `ethereum/pm` via the GitHub API, parses the date, agenda and meeting links from each issue body, and returns a valid ICS calendar on the fly.
