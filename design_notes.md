Game State diagram

Available Game States:
  - INITIAL_ARMY_PLACEMENT
  - INITIAL_ARMY_FORTIFICATION
  - PLAYER_CARD_CHECK
  - PLAYER_PLACE_NEW_ARMIES
  - PLAYER_ATTACKING
  - PLAYER_FORTIFICATION

Available Player States:
  - INITIAL_ARMY_PLACEMENT
  - INITIAL_ARMY_FORTIFICATION
  - PLAYER_CARD_CHECK
  - PLAYER_PLACE_NEW_ARMIES
  - PLAYER_ATTACKING_FROM
  - PLAYER_ATTACKING_WITH
  - PLAYER_ATTACKING_TO
  - PLAYER_MOVING_POST_WIN
  - PLAYER_FORTIFICATION_FROM
  - PLAYER_FORTIFICATION_WITH
  - PLAYER_FORTIFICATION_TO
  - PLAYER_CARD_PICK

Card States:
  - PLAYER_CANT_USE_CARDS
  - PLAYER_CAN_USE_CARDS
  - PLAYER_MUST_USE_CARDS

Game Outline
```mermaid
flowchart TD
    A[Game Start] --> B[Initial Army Placement]
    B -- "Increment Player (Until All Armies Placed)" --> B
    B -- "Armies Placed" --> C[Initial Army Fortification]
    C -- "Increment Player (Through List Once)" --> C
    C --> D
    
    subgraph "Player Turns"
        subgraph "Player Card Phase"
            D[Player Card Check] -- "Player Can Use Cards" --> E[Player Decides on Using Cards]
            D -- "Player Can't Use Cards" --> G
            D -- "Must Use Cards" --> F[Player Decides Which Cards]
            F --> G
            E -- "Player Picked to Use Cards" --> F
            E -- "Player Picked Not to Use Cards" --> G
        end
        

            G[Player Places New Armies] -- "Increment through Armies" --> G
            G -- "Player Placed All Armies" --> H
        
        subgraph "Player Attacking Turn"
            H[Player Attacking From] -- "Player Decides to Attack" --> I
            I[Player Attacking With] --> J
            J[Player Attacking To]--> H
        end
        
        subgraph "Player Fortification Phase"
            H -- "Player Declines to Attack" --> K[Player Fortification From]
            K -- "Player Decides to Fortify" --> L[Player Fortification With]
            L -- "Player Decides to Fortify" --> M[Player Fortification To]
        end
        
        K -- "Player Declines to Fortify" --> D
        M -- "Player Finished Fortifying" --> D
        
        H -- "No Teams Left to Attack" --> N[Player Won]
        
        
    end
```
