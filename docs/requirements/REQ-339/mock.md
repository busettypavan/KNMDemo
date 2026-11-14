# REQ-339 mock: Account sign-up and sign-in

```
+------------------------------------------------+
|  KNMDemo                                       |
+------------------------------------------------+
|                                                |
|   [ Sign in ]   [ Create account ]             |
|   ------------                                 |
|                                                |
|   Email                                        |
|   [______________________________________]     |
|                                                |
|   Password                                     |
|   [______________________________________]     |
|                                                |
|   [            Sign in            ]            |
|                                                |
|   New investor? Create account                 |
|                                                |
+------------------------------------------------+

Create account tab (same screen, second tab):

|   Email                                        |
|   [______________________________________]     |
|   Password                                     |
|   [______________________________________]     |
|   [         Create account         ]           |

Flow:
  Create account --> signed in --> positions and preferences saved to account
  Sign in        --> signed in --> positions and preferences restored
```
