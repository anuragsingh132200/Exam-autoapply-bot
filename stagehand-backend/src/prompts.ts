/**
 * Robust Prompt Builders for Stagehand Actions
 * 
 * These prompts are designed to be precise and foolproof.
 * Stagehand works best with clear, specific natural language instructions.
 */

/**
 * Build a robust prompt for filling a form field
 */
export function buildFillPrompt(fieldLabel: string, value: string): string {
    // Sanitize value - escape quotes
    const sanitizedValue = value.replace(/"/g, '\\"');
    const labelLower = fieldLabel.toLowerCase();

    // Special handling for confirm/re-enter fields
    if (labelLower.includes("confirm") || labelLower.includes("re-enter") || labelLower.includes("retype")) {
        return `Find the SECOND input field that asks to confirm or re-enter the value. Look for fields labeled "confirm ${labelLower.replace("confirm ", "")}", "re-enter", "retype", or a second field after the primary one. Type "${sanitizedValue}" into this confirmation field. Clear any existing text first.`;
    }

    // Build comprehensive prompt that handles various field types
    return `Find the input field labeled "${fieldLabel}" or with placeholder containing "${fieldLabel}" and type "${sanitizedValue}" into it. If it's a dropdown/select, choose the option "${sanitizedValue}". If the field already has text, clear it first before typing.`;
}

/**
 * Build a robust prompt for clicking a button
 */
export function buildClickButtonPrompt(buttonText: string): string {
    return `Click the button that contains the text "${buttonText}". Look for buttons, links, or clickable elements with this text. If there are multiple matches, click the most prominent or primary one.`;
}

/**
 * Build a robust prompt for checking a checkbox
 */
export function buildCheckboxPrompt(checkboxLabel: string): string {
    const labelLower = checkboxLabel.toLowerCase();

    // For declaration/agreement checkboxes
    if (labelLower.includes("hereby") || labelLower.includes("declare") || labelLower.includes("agree") || labelLower.includes("terms")) {
        return `Find and click the unchecked checkbox next to the declaration or agreement text that contains "${checkboxLabel.substring(0, 50)}...". This is usually at the top or bottom of the form. Look for a checkbox input element or a clickable square/box. Click it to check/select it.`;
    }

    return `Find and click the checkbox associated with "${checkboxLabel}". This might be a checkbox input, a clickable label, or a custom checkbox element. Make sure it becomes checked/selected after clicking.`;
}

/**
 * Build a robust prompt for typing into OTP field
 */
export function buildOtpPrompt(otp: string): string {
    return `Find the OTP input field (it may be labeled "OTP", "Verification Code", "One Time Password", or be a series of single-digit input boxes) and enter "${otp}". If there are multiple single-digit boxes, enter each digit in sequence.`;
}

/**
 * Build a robust prompt for typing captcha solution
 */
export function buildCaptchaPrompt(solution: string): string {
    return `Find the captcha input field (usually near a captcha image, labeled "Enter Captcha", "Security Code", or similar) and type "${solution}" into it.`;
}

/**
 * Build a robust prompt for clicking submit/continue button
 */
export function buildSubmitPrompt(): string {
    return `Click the submit, continue, next, or proceed button. Look for the primary action button on the page - it's usually a prominent button at the bottom of a form with text like "Submit", "Continue", "Next", "Proceed", "Register", "Sign Up", or "Apply".`;
}

/**
 * Build a robust prompt for selecting a dropdown option
 */
export function buildSelectPrompt(fieldLabel: string, optionValue: string): string {
    return `Find the dropdown/select field labeled "${fieldLabel}" and select the option "${optionValue}". Click the dropdown first to open it, then click the matching option.`;
}

/**
 * Build observation prompt for page analysis
 */
export function buildObservePrompt(): string {
    return `Identify all interactive elements on this page including:
- Input fields (text, email, phone, password, date)
- Dropdown/select menus
- Checkboxes and radio buttons
- Buttons (especially submit, continue, next buttons)
- Any captcha or OTP fields
- Error messages or validation messages
Return a list of what you found with their labels/text.`;
}

/**
 * Build extraction prompt for page state
 */
export function buildExtractPageStatePrompt(): string {
    return `Analyze this page and determine:
1. The page type (login, registration form, OTP verification, captcha, success page, error page)
2. Are there any unfilled required form fields?
3. Is there a captcha that needs solving?
4. Is there an OTP/verification code input?
5. What is the main action button text?
6. Are there any error messages displayed?`;
}

/**
 * Map common field keys to natural language labels
 */
export function normalizeFieldLabel(fieldKey: string): string {
    const mappings: Record<string, string> = {
        // Personal Info
        "name": "full name",
        "fullName": "full name",
        "full_name": "full name",
        "firstName": "first name",
        "first_name": "first name",
        "lastName": "last name",
        "last_name": "last name",

        // Contact
        "email": "email address",
        "emailAddress": "email address",
        "email_address": "email address",
        "confirmEmail": "confirm email address",
        "confirm_email": "confirm email address",
        "emailConfirm": "confirm email address",
        "reenterEmail": "re-enter email address",
        "phone": "phone number",
        "mobile": "mobile number",
        "mobileNumber": "mobile number",
        "mobile_number": "mobile number",
        "phoneNumber": "phone number",
        "phone_number": "phone number",
        "confirmPhone": "confirm phone number",
        "confirm_phone": "confirm phone number",

        // Address
        "address": "address",
        "city": "city",
        "state": "state",
        "pincode": "pincode",
        "zipcode": "zip code",
        "zip": "zip code",
        "country": "country",

        // Identity
        "dob": "date of birth",
        "dateOfBirth": "date of birth",
        "date_of_birth": "date of birth",
        "gender": "gender",
        "nationality": "nationality",

        // Education
        "qualification": "qualification",
        "education": "education",
        "degree": "degree",
        "college": "college name",
        "university": "university name",
        "passingYear": "passing year",
        "passing_year": "passing year",
        "percentage": "percentage",
        "cgpa": "CGPA",

        // Documents
        "aadhar": "Aadhar number",
        "aadharNumber": "Aadhar number",
        "pan": "PAN number",
        "panNumber": "PAN number",
        "passport": "passport number",

        // Exam specific
        "examCenter": "exam center",
        "exam_center": "exam center",
        "category": "category",
        "subcategory": "subcategory",
    };

    return mappings[fieldKey] || fieldKey.replace(/([A-Z])/g, ' $1').replace(/_/g, ' ').trim().toLowerCase();
}
