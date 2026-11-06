# Proof of Learning: Creative Complaint Handler

## Implementation

`normalobjects_langchain.py` defines four tools for Hawkins records, party advice, Demogorgon opinions, and interdimensional spells. A LangChain agent built with `create_agent` and `ChatOpenAI` chooses tools for each complaint. The script prints tool calls, returned outputs, and the final response. It loads the API key from `.env`; `.gitignore` excludes that file.

## Recorded run

**Query:** The power in my house flickers whenever my psychic cousin visits.

The agent selected these tools:

```text
check_hawkins_records({'query': 'electricity'})
gather_party_wisdom({'question': 'What to do about flickering power when a psychic is around?'})
cast_interdimensional_spell({'problem': 'flickering power when a psychic cousin visits', 'creativity_level': 'medium'})
```

Their actual outputs were:

```text
check_hawkins_records: Hawkins records report that unusual electrical surges can precede a portal disturbance.
gather_party_wisdom: The party suggests a quick huddle, a map, and not investigating the noise alone.
cast_interdimensional_spell: Play one calm song toward flickering power when a psychic cousin visits and close the nearest wardrobe for good measure.
Draw a chalk circle around flickering power when a psychic cousin visits and appoint a toy knight as guard.
```

The agent's actual final response was:

> It seems your psychic cousin's visits might be causing some unusual electrical surges, possibly hinting at a portal disturbance! The party suggests gathering together for safety and not investigating any strange noises alone.
>
> To tackle the flickering power, here are a couple of playful spells you can try:
>
> 1. **Calm Song Charm**: Play a soothing song towards the flickering power while closing the nearest wardrobe for good.
> 2. **Chalk Circle Guard**: Draw a chalk circle around the flickering area and appoint a toy knight as your trusty guard.
>
> These whimsical solutions might just help keep the energy stable during your cousin's visits!

## Evidence and limitation

The records output supports the mention of electrical surges and a possible portal disturbance. The two spell suggestions correspond to the spell tool's calm-song and chalk-circle outputs. The party advice is the tool's generic fallback. Its lookup checks for the key `psychics`, but the question used `psychic`, so it did not return a character-specific answer. The record also says surges can precede a disturbance; it does not establish that the cousin caused them.
