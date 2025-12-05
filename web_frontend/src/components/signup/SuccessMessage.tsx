import { Link } from "react-router";
import type { SignupFormData } from "../../types/signup";

interface SuccessMessageProps {
  formData: SignupFormData;
}

export default function SuccessMessage({ formData }: SuccessMessageProps) {
  const totalSlots = Object.values(formData.availability).reduce(
    (sum, slots) => sum + slots.length,
    0,
  );

  return (
    <div className="max-w-md mx-auto text-center">
      <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
        <svg
          className="w-8 h-8 text-green-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M5 13l4 4L19 7"
          />
        </svg>
      </div>

      <h2 className="text-2xl font-bold text-gray-900 mb-2">You're All Set!</h2>
      <p className="text-gray-600 mb-8">
        Your signup has been submitted successfully.
      </p>

      <div className="bg-gray-50 rounded-lg p-4 mb-8 text-left">
        <h3 className="font-medium text-gray-900 mb-3">Summary</h3>
        <dl className="space-y-2 text-sm">
          {formData.firstName && (
            <div className="flex justify-between">
              <dt className="text-gray-500">First Name</dt>
              <dd className="text-gray-900">{formData.firstName}</dd>
            </div>
          )}
          {formData.lastName && (
            <div className="flex justify-between">
              <dt className="text-gray-500">Last Name</dt>
              <dd className="text-gray-900">{formData.lastName}</dd>
            </div>
          )}
          <div className="flex justify-between">
            <dt className="text-gray-500">Discord</dt>
            <dd className="text-gray-900">
              {formData.discordConnected
                ? formData.discordUsername
                : "Not connected"}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">Available Time Slots</dt>
            <dd className="text-gray-900">{totalSlots} slots selected</dd>
          </div>
        </dl>
      </div>

      <Link
        to="/"
        className="inline-block px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg transition-colors"
      >
        Return to Home
      </Link>
    </div>
  );
}
