# DanceDance1

| Role  | Person |
| ------------- | ------------- |
| AI Aficionado  | Melvin  |
| AI Aficionado  | Srishti  |
| Power Pro | Zhi Wei |
| Sensor Superman | Jia Hao |
| Comms Champion | Zuo Xuan |
| Comms Champion | Justin |

## Housekeeping
1) Please organize your files into your sections: `comms`, `software`, `hardware`
2) Commit your work to the `dev` branch and submit PRs to `master` after your counterpart has reviewed.

## Moves
- Chicken
- Cowboy
- Crab
- Doublepump
- Hunchback
- Jamesbond
- Mermaid
- Raffles
- Runningman
- Snake
- Stationary (default move that is not recognized by the server)
- Ultimate

The "Ultimate" move is simply a vertical, oscillating movement of the left hand above the head, with the right hand (palm-facing up) at the abdomen as though the dancer had stabbed themself.

## Communication Protocol
Communication protocol is JZON1.2. Packets follow the following convention:
```
[57][PACKET_CODE][LEN][DATA]
```
and are responded to with either an `ACK`, `NACK`, or `RESET`.

## Data Collection and Training
When collecting data for the ML model we simply run a test file (which dumps output data to console in pseudo-JSON) adapted to save the output to a `.out` file.

Assuming `test` is an alias of `python3 test_comms.py`,

```
test >&1 | tee ../data/transient/<username>_<movename>.out
```

After collection simply convert the outfile to JSON by replacing `'` with `"`, adding commas to the end of each line, and adding `[]` to encapsulate the contents of the file. Finally, rename the extension from `.out` to `.json`. Melvin will use this for his training model.
