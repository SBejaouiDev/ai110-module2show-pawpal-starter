# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
Consider constraints (time available, priority, owner preferences)
Produce a daily plan and explain why it chose that plan




- What classes did you include, and what responsibilities did you assign to each?

1) Pet
    - Atributes 
        - Name 
        - Type  
        - weight

2) scheduler
    - methods
        - walk 
        - meds
        - feeding 
        - grooming 
        - enrichment

3) task

    - methods
        - view Tasks
        - add tasks 
        - remove tasks 
        - sort tasks 


4) Owner
    - Atributes 
        - avalability  
        - scheduler  (reference to a Scheduler — association)
        - task       (reference to a Task — association)

    - methods
        - add pet 
        - remove pet 


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

    Prior to prompting claude, I didnt specifify the assocations correctly and didnt provide return types for the scheduler and task methods. A class called scheduledTasks was created and returns types were added. 



---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
    Filter tasks by pet

- Why is that tradeoff reasonable for this scenario?
    If a owner has multiple pets allows for quick look up.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
    For simple projects like this the outputs the models gave me were accurate and not error prone. Did not have to do much debugging. For brainstorming I drafted most of the features and then asked for any suggestions on those features I had drafted. 

- What kinds of prompts or questions were most helpful?
    - Explain this provide an example 
    - Provide pros and cons to this design approach
    - what are edge cases I am missing 
    - How can I improve this design feature 
    

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
    - Tasks with the same date and time
    - Overdue tasks
- Why were these tests important?
    Important overdue tasks such as feeding and medication need to be taken care of. Tasks with the same time and date cause scheduling conflitct. 

**b. Confidence**

- How confident are you that your scheduler works correctly?
    5 
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
    - The planning process was engaging. It provides a small gimplse of how larger systems can be build following a structured layout. Even for such a simple app like paypal, there were many edge cases to look out for. Jumping straight into development could have been a nightmare. 

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
    - I dont care too much about the UI. I believe if someone were to use this app they would not stick with it due to its confusing layout and unappealing visuals. UI experience makes or breaks an app

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
    Planning is important. Jumping straight to coding can create holes in your project. Developing a great foundation is key, this allows you to add features later on without breaking your existing code base. 