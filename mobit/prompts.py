page_segmentation = """
I will provide you with a page screenshot and its corresponding XML layout file. Based on these inputs, please perform the following analysis and return structured output:

 **Page Functionality Module Recognition and Interactive Element Identification**:
   - Identify **all functional modules** on the page based on the screenshot and XML layout.**Prioritize** them based on user usage habits.Do not omit any module or interactive element.
   - For each **functional module**, identify **all interactive elements**.
   - For each **functional module**, provide a **UI Test Plan** that includes:
     - **a.Bounds**: The `bounds` attribute from the XML file, which gives the coordinates and size of the functional module.
     - **b.Index**: The `index` attribute, which represents the position of the module in the layout hierarchy.
     - **c.Test Plan Type**:
          c-1. **Random Click**: should be used for elements that are functionally similar, where only one needs to be tested at a time.
          c-2. **Sequential Click**:for elements with different functions, where each element needs to be tested sequentially for its unique functionality.
          c-3. **Other**: reserved for more complex scenarios, like form filling, that require detailed, step-by-step testing.
     - **d.The interactive elements** for each functional module should be listed by their **index** only, without needing to list other properties (e.g., resource-id, content-desc, etc.).    

Return the results in the following structured JSON format:
{
    "page_overview": "This login page is designed to authenticate users by allowing them to enter their credentials. It features distinct input fields for the username and password, a prominent login button to submit the credentials, and a 'Forgot Password' link to assist users in recovering their account access. These interactive elements are integral to the authentication process, ensuring that users can securely log in and access their personalized dashboard.",
    "functional_modules": [
        {
            "module_name": "Login Module",
            "bounds": "[0, 0][100, 50]",
            "index": "0-1",
            "interactive_elements": [#Important**: For the **interactive_elements** field, ensure that you only include the index values that exist in the provided **XML layout file**. These indices are the crucial basis for identifying the interactive elements.
                "0-1-0",
                "0-1-2"
            ],
            "test_plan": {
                "type": "Random Click",
                "steps": [
                    "Click on the login button",
                    "Verify that the login action is triggered"
                ]
            }
        }
    ]
}
if you cannot find any functional modules, return:
{
    "functional_modules": []
}
"""

representative_ui_elements='''
I will provide you with a page screenshot and its corresponding XML layout file. Based on these inputs, please perform the following analysis and return structured output:

 - **Comprehensive Elements for Repeat Page Detection** 
    - Based on the UI screenshot and XML layout, identify all representative UI elements that remain stable across different sessions and are capable of distinguishing one page from another or identifying the same page when revisited.
    - Classify these elements into three categories:
        Title: Typically a static, prominent text or label that indicates the page’s primary purpose (e.g., “Login,” “Product Details”).
        Primary_Action_Button: A key interactive element, such as “Submit,” “Next,” or “Buy,” which plays a critical role in user flow.
        Fixed_Layout_Components: Commonly stable layout elements like a navigation bar, tool bar, or fixed banner.
    - Include as many elements as possible that may provide stable identifying properties. If truly no element qualifies for a category, you may omit that category. However, borderline cases or partially suitable elements should still be included if they offer potential value for repeat page detection.
    - Instead of other identifiers, use the XML index attribute to uniquely specify each element in the output.


Please carefully select only attributes that are stable, representative, static, and available directly on the element itself according to the XML data provided. There is no need to list all given attributes; include only those you deem genuinely representative and stable.
Return the results in the following structured JSON format:
{
    "representative_ui_elements": {
        "Title": [
            "0-1",
            "0-2",
            "0-3"
        ],
        "Primary_Action_Button": [],
        "Fixed_Layout_Components": []
    }
}
if you cannot find any representative ui elements, return:
{
    "representative_ui_elements": {
        "Title": [],
        "Primary_Action_Button": [],
        "Fixed_Layout_Components": []
    }
}
'''

next_action = """
Background Context:
The task is to perform actions in a Target_Area of the UI that links to distinct views. To ensure that all elements are explored efficiently, given the constraints of performing no more than 10 actions. Maintains the action limit by focusing on essential interactions that provide the most information about the UI’s behavior.
you need to avoid redundant actions based on Action History.

In this UI functionality testing task, you'll receive:
- Action History,
- A screenshot.
- A view hierarchy file.
- App Information.
- the Target Area in the page,
- Page Segmentation in the page with the following structure,Do not add comments in JSON format data: 
[{
    "Bounds":..., # 'bounds' attribute value of the element for this area from view hierarchy file. The bounds are given in the format \"[left,top][right,bottom]\" as per the Android view hierarchy convention.
    "Observation": ...  # Describe what you observe in this region,
    "Documentation": ...  # Describe the functions of the region,
    "Elements": Lists all elements without omitting in the area, list only the index field from the view hierarchy file such as ['0-0-0-0-1','0-0-0-0-2','0-0-0-0-3'],No count values beyond those present in the view hierarchy file are included in the returned content.
    "Container":... # the index field of the element that is the container of the region,
    "Thought": Outlines the planned approach for testing,You cannot output anything else except 'click_each' or 'click_select' or 'others'.
    "Explain":Explain why you chose 'click_each' or 'click_select' or 'others',
}]

You can call the following functions to interact with elements to control the smartphone:

1. tap(element: str)
This function is used to tap an UI element shown on the smartphone screen.
"element" is the 'index' attribute value of the element based on Current_Page_hierarchy. It is important to ensure that the element specified actually exists within the current view hierarchy.
A simple use case can be tap('0-1'), which taps the UI element with the 'index' attribute value '0-1'.

2. text(text_input: str)
This function is used to insert text input in an input field/box. text_input is the string you want to insert and must 
be wrapped with double quotation marks. A simple use case can be text("Hello, world!"), which inserts the string 
"Hello, world!" into the input area on the smartphone screen. This function is only callable when you see a keyboard 
showing in the lower half of the screen.

3. long_press(element: str)
This function is used to long press an UI element shown on the smartphone screen.
"element" is the 'index' attribute value of the element based on Current_Page_hierarchy. It is important to ensure that the element specified actually exists within the current view hierarchy.
A simple use case can be long_press('0-1'), which long presses the UI element with the 'index' attribute value '0-1'.

4. swipe(element: str, direction: str, dist: str)
This function is used to swipe an UI element shown on the smartphone screen, usually a scroll view or a slide bar.
"element" is the 'index' attribute value of the element based on Current_Page_hierarchy. It is important to ensure that the element specified actually exists within the current view hierarchy.
"direction" is a string that represents one of the four directions: up, down, left, right. "direction" must be wrapped with double quotation 
marks. "dist" determines the distance of the swipe and can be one of the three options: short, medium, long. You should 
choose the appropriate distance option according to your need.
A simple use case can be swipe('0-1', "up", "medium"), which swipes up the UI element with the 'index' attribute value '0-1' for a medium distance.

Return the results in JSON format with the following structure: 
{
    "Observation": <Describe what you observe in the image>
    "Thought": <To complete the given task, what is the next step I should do>
    "Action": <The function call with the correct parameters to proceed with the task. If you believe the task is completed or 
    there is nothing to be done, you should output FINISH. You cannot output anything else except a function call or FINISH 
    in this field.>
    "Summary": <Summarize your past actions along with your latest action in one or two sentences. Do not include the numeric 
    tag in your summary>
}
if you cannot find any functional modules, return:
{
    "Observation": <Describe what you observe in the image>
    "Thought": <To complete the given task, what is the next step I should do>
    "Action": "FINISH"
    "Summary": <Summarize your past actions along with your latest action in one or two sentences. Do not include the numeric 
    tag in your summary>
}
"""

logic_graph_generation = """
You are an intelligent assistant familiar with UI page function identification and function logic diagram construction. You will now combine the provided mobile App page screenshots and related descriptive information to strictly follow the steps below to construct a complete and precise function logic diagram (including independent isolated functions, such as features within a page that can be used independently without navigating to other pages):

You will receive the following information:

1. Page Screenshot: Interactive controls on the current page are clearly marked with red boxes in the format "{action_id}-p{target_page_id}" indicating the operation and target page.
2. All Target Page Screenshot Collage: Screenshots are stitched together, and below each image is a clear operation sequence number and page ID (action_id target_page_id).
3. Operation Information List: Each operation record includes the source page ID, target page ID, action_id, action type, and specific control text.
4. Current Existing Function Logic Diagram: The existing diagram records current function nodes and their business transition relationships.
5. Related Page Function Descriptions: Brief page function descriptions, which may include independent logic-completing functions without page transitions (such as search, refresh, display mode switch, etc.).

Please strictly follow the steps below to execute the task:

Step 1: Identify Functional Nodes (including isolated functional nodes)
- Based on the provided page function descriptions, screenshots, and operation information:
    - Extract in-page business functions (especially those that do not result in navigation and can independently complete a business logic, such as search, pull-to-refresh, etc.), and generate corresponding function node descriptions.
    - Function Merging: If some operations have the same effect, target page, and execution path, merging them in the function logic diagram is recommended.
    - If a target page ID is not yet in the function logic diagram, generate a new function node based on the page description and use the page_id marked in the screenshot to label it (e.g., "page_id": 3). Ensure every function node includes a clear functional description.

Step 2: Map Page Transition Relationships

- Based on the red box markings in the page screenshots "{action_id}-p{target_page_id}", strictly verify and map the transitions between the source and target pages.
- If the page jump operation corresponds to a duplicate or overlapping function point, merge them to avoid redundant nodes.

Step 3: Update the Function Logic Diagram

- Integrate the newly identified function nodes (including isolated nodes) and page relationships into the existing logic diagram.
- page_id and action_id must strictly match the IDs provided in the screenshots without modification.
- Ensure all function nodes and page relationships are accurately reflected in the final function logic diagram, with no omissions or redundancies.

Output Requirements:

- Output must strictly follow the JSON format below. Do not include extra explanations or comments, and accurately cite all page_ids from the screenshots:

{
    "function_nodes": [{
        "function_id": "Function node ID, starting from 0 in ascending order",
        "function_name": "Function name or clear business logic description",
        "related_pages": [{
            "page_id": "Strictly use the ID from the screenshot, such as '1', without modification or omission",
            "page_name": "Clear and accurate page name or description"
        }]
    }],
    "logic_relations": [{
        "source_function_id": "Source function node ID",
        "target_function_id": "Target function node ID",
        "description": "Describe the business logic transition or interaction scenario between the two function nodes",
        "operation_description": "Click [Product Selection] button"
    }]
}

Notes:

* Must clearly identify and express in-page independent function nodes—do not omit any.
* Must strictly and accurately use the "{action_id}-p{target_page_id}" information in the screenshots for page ID validation—do not create new IDs or omit existing ones.
* The output must not contain any page_id or action_id information that does not match the screenshot labels.

Now please complete the task according to the above rules.

"""

logic_path_generation = """
As an intelligent assistant for automatically generating UI test business logic paths, you will be provided with a complete function logic diagram and serialized function node information.

You need to complete the following task:

Based on the provided function logic diagram, list in JSON format every real and meaningful business operation path from a starting point to an endpoint.

Each path must meet the following criteria:

* The start and end of the path must represent clearly defined beginning and end points of a real user business scenario, determined based on actual business logic.
* The overall sequence of the path must strictly follow the execution order of each function step in real business logic. For example, if there is a dependency between functions, the prerequisite function must appear before the dependent one (e.g., creating a new item must come before sorting or searching).
* The function path description must concisely and accurately describe the details of the actual business process. Avoid vague or abstract descriptions.
* The "expected_result" field is used to describe the expected goal or result at the endpoint of the path. Use clear and precise language to describe what the user will see on the UI after completing this task.

Please provide each path in the following JSON format:

{
    "functional_logic_paths": [{
        "path_id": 0,
        "start_function_id": 0,
        "end_function_id": 2,
        "path_description": "Enter the product page from the homepage and submit an order after selecting a product",
        "expected_result": "Display order submission success message and related information"
    }]
}

"""

step_desc_generation = """
You are now acting as an intelligent assistant for automatically generating UI test business logic paths. I will provide a complete business logic diagram and the serialized functional node information.

Based on the start and end path data previously identified and extracted, you are to return the specific functional flow node steps, strictly following the logic and constraints below:

**You must strictly adhere to the following logic and constraints:**

**a. Path Integrity Constraint**
Each functional business logic path you design must start from the given start_function_id and end at the given end_function_id from Step 1. You must not omit any key steps. All required functional nodes must be completely included.

**b. State Transition Validity Constraint**
Each transition between functional nodes in the path must correspond to a real, executable UI operation. No imaginary or unimplemented UI jumps are allowed.

**c. Logical Rationality Constraint**
Each function operation must comply with real business logic and typical user behavior. The sequence of operations must be continuous and logical. Skipping essential steps or jumping too far—making the flow unusable for users—is not allowed.

Please follow the JSON format example below to detail each path's functional steps. Clearly specify the operation required at each node:

{
    "steps": [
        {
            "step_id": 0,
            "function_id": 0,
            "function_name": "Home Page",
            "operation_description": "Click the [Product Selection] button"
        },
        {
            "step_id": 1,
            "function_id": 1,
            "function_name": "Product Selection Page",
            "operation_description": "After selecting a product, click the [Confirm Submit Order] button"
        },
        {
            "step_id": 2,
            "function_id": 2,
            "function_name": "Order Submission Confirmation Page",
            "operation_description": "Page loads and displays order submission confirmation"
        }
    ]
}

"""
defect_detection = """
You are an intelligent assistant for UI defect detection. You will analyze the provided logic paths and their corresponding screenshots to identify potential defects in the application.

You will receive the following information:
1. Logic Path Information:
   - Complete path description
   - Step-by-step operation details
   - Expected results for each path
2. Path Screenshots:
   - Screenshots are stitched together in sequence
   - Each image has clear action descriptions below it

Defects:
- Content Display Error: Text is unreadable or displays as garbled characters (e.g., ‘□□□□’, null, or HTML entities), or appears in incorrect or unexpected formats.
- UI Layout Issue: Overlapping, misaligned, or unevenly spaced elements clutter the page and obscure content. For example, an image or text element overlaps another, or similar elements have inconsistent spacing.
- UI Element Missing: Essential UI element is absent, causing functionality issues or abnormal blank spaces. For example, image not loaded or displayed broken.
- UI Consistency Issue: Inconsistent colors, element sizes, or states. For example, some navigation icons have different colors, font sizes vary, or a button appears active without interaction.
- Operation No Response: No feedback or action follows user interaction.
- Navigation Logic Error: Navigation logic flaw leads to incorrect application flow.
- Unexpected Task Result: Task result do not match expected outcome.

Please return the defects in the following JSON format:
{
    "defects": [
        {
            "step_id": "The step ID where the defect occurs",
            "page_id": "The ID of the page containing the defect",
            "defect_type": "One of the defect categories listed above",
            "reason": "The reason why you think this is a defect",
            "fix_suggestion": "The suggestion for fixing the defect"
        },
        
    ]
}
If NO defect is observed, return:
{
    "defects": []
}
"""