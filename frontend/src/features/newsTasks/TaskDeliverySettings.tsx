import {
  FormControl,
  FormLabel,
  Switch,
  Select,
  VStack,
  Text,
  Textarea,
} from '@chakra-ui/react';
import {
  DEFAULT_TELEGRAM_SUMMARY_PROMPT,
  type NewsTaskSettings,
} from '../../types';

const TELEGRAM_LANGUAGE_OPTIONS = [
  { value: 'en', label: 'English' },
  { value: 'zh', label: 'Chinese (Mandarin)' },
  { value: 'hi', label: 'Hindi' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
  { value: 'ar', label: 'Arabic' },
  { value: 'bn', label: 'Bengali' },
  { value: 'pt', label: 'Portuguese' },
  { value: 'ru', label: 'Russian' },
  { value: 'ur', label: 'Urdu' },
  { value: 'id', label: 'Indonesian' },
  { value: 'de', label: 'German' },
  { value: 'ja', label: 'Japanese' },
  { value: 'sw', label: 'Swahili' },
  { value: 'mr', label: 'Marathi' },
  { value: 'te', label: 'Telugu' },
  { value: 'tr', label: 'Turkish' },
  { value: 'ta', label: 'Tamil' },
  { value: 'vi', label: 'Vietnamese' },
  { value: 'ko', label: 'Korean' },
  { value: 'it', label: 'Italian' },
  { value: 'fa', label: 'Persian (Farsi)' },
  { value: 'pl', label: 'Polish' },
  { value: 'uk', label: 'Ukrainian' },
  { value: 'nl', label: 'Dutch' },
  { value: 'th', label: 'Thai' },
  { value: 'ms', label: 'Malay' },
  { value: 'ro', label: 'Romanian' },
  { value: 'he', label: 'Hebrew' },
  { value: 'cs', label: 'Czech' },
  { value: 'el', label: 'Greek' },
  { value: 'hu', label: 'Hungarian' },
  { value: 'sv', label: 'Swedish' },
  { value: 'da', label: 'Danish' },
  { value: 'fi', label: 'Finnish' },
  { value: 'no', label: 'Norwegian' },
  { value: 'sk', label: 'Slovak' },
  { value: 'bg', label: 'Bulgarian' },
  { value: 'hr', label: 'Croatian' },
  { value: 'sr', label: 'Serbian' },
  { value: 'sl', label: 'Slovenian' },
  { value: 'lt', label: 'Lithuanian' },
  { value: 'lv', label: 'Latvian' },
  { value: 'et', label: 'Estonian' },
  { value: 'ca', label: 'Catalan' },
  { value: 'eu', label: 'Basque' },
  { value: 'gl', label: 'Galician' },
  { value: 'is', label: 'Icelandic' },
  { value: 'ga', label: 'Irish' },
  { value: 'cy', label: 'Welsh' },
  { value: 'mt', label: 'Maltese' },
  { value: 'sq', label: 'Albanian' },
  { value: 'mk', label: 'Macedonian' },
  { value: 'ka', label: 'Georgian' },
  { value: 'hy', label: 'Armenian' },
  { value: 'az', label: 'Azerbaijani' },
  { value: 'kk', label: 'Kazakh' },
  { value: 'uz', label: 'Uzbek' },
  { value: 'ky', label: 'Kyrgyz' },
  { value: 'mn', label: 'Mongolian' },
  { value: 'ne', label: 'Nepali' },
  { value: 'si', label: 'Sinhala' },
  { value: 'my', label: 'Burmese' },
  { value: 'km', label: 'Khmer' },
  { value: 'lo', label: 'Lao' },
  { value: 'am', label: 'Amharic' },
  { value: 'yo', label: 'Yoruba' },
  { value: 'ig', label: 'Igbo' },
  { value: 'ha', label: 'Hausa' },
  { value: 'zu', label: 'Zulu' },
  { value: 'af', label: 'Afrikaans' },
  { value: 'so', label: 'Somali' },
  { value: 'ps', label: 'Pashto' },
  { value: 'pa', label: 'Punjabi' },
  { value: 'gu', label: 'Gujarati' },
  { value: 'kn', label: 'Kannada' },
  { value: 'ml', label: 'Malayalam' },
  { value: 'or', label: 'Odia' },
  { value: 'as', label: 'Assamese' },
  { value: 'jv', label: 'Javanese' },
  { value: 'su', label: 'Sundanese' },
  { value: 'fil', label: 'Filipino' },
  { value: 'be', label: 'Belarusian' },
  { value: 'bs', label: 'Bosnian' },
  { value: 'lb', label: 'Luxembourgish' },
  { value: 'xh', label: 'Xhosa' },
  { value: 'mi', label: 'Maori' },
  { value: 'sm', label: 'Samoan' },
  { value: 'ht', label: 'Haitian Creole' },
  { value: 'la', label: 'Latin' },
];

interface TaskDeliverySettingsProps {
  settings: NewsTaskSettings;
  onChange: (settings: NewsTaskSettings) => void;
}

export const TaskDeliverySettings = ({
  settings,
  onChange,
}: TaskDeliverySettingsProps) => {
  const telegram = settings.delivery.telegram;

  return (
    <VStack spacing={4} align="stretch">
      <Text fontSize="sm" color="gray.600">
        Configure how this task is delivered to Telegram.
      </Text>

      <FormControl display="flex" alignItems="center" justifyContent="space-between">
        <FormLabel mb="0">Send summary (plain link if off)</FormLabel>
        <Switch
          isChecked={telegram.summary}
          onChange={(e) =>
            onChange({
              ...settings,
              delivery: {
                ...settings.delivery,
                telegram: {
                  ...telegram,
                  summary: e.target.checked,
                  prompt:
                    telegram.prompt || DEFAULT_TELEGRAM_SUMMARY_PROMPT,
                },
              },
            })
          }
        />
      </FormControl>

      {telegram.summary ? (
        <FormControl>
          <FormLabel>Customize summary prompt</FormLabel>
          <Textarea
            value={telegram.prompt || DEFAULT_TELEGRAM_SUMMARY_PROMPT}
            onChange={(e) =>
              onChange({
                ...settings,
                delivery: {
                  ...settings.delivery,
                  telegram: {
                    ...telegram,
                    prompt: e.target.value,
                  },
                },
              })
            }
            placeholder={DEFAULT_TELEGRAM_SUMMARY_PROMPT}
            rows={3}
          />
          <Text fontSize="xs" color="gray.500" mt={1}>
            Leave unchanged to use the default prompt.
          </Text>
        </FormControl>
      ) : null}

      <FormControl>
        <FormLabel>Telegram language</FormLabel>
        <Select
          value={telegram.lang}
          onChange={(e) =>
            onChange({
              ...settings,
              delivery: {
                ...settings.delivery,
                telegram: {
                  ...telegram,
                  lang: e.target.value,
                },
              },
            })
          }
        >
          {TELEGRAM_LANGUAGE_OPTIONS.map((language) => (
            <option key={language.value} value={language.value}>
              {language.label}
            </option>
          ))}
        </Select>
      </FormControl>
    </VStack>
  );
};
