import { useEffect, useState } from 'react';
import {
  Alert,
  AlertDescription,
  AlertIcon,
  Box,
  Button,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Spinner,
  Text,
  Textarea,
  VStack,
  useToast,
  Center,
} from '@chakra-ui/react';
import {
  useGetCurrentUserQuery,
  useUpdateCurrentUserMutation,
} from '../../services/api';
import type { UserSettings } from '../../types';

interface SettingsFormState {
  geminiApiKey: string;
  telegramApiId: string;
  telegramApiHash: string;
  telegramSessionString: string;
  telegramBotToken: string;
}

type SettingsField = keyof SettingsFormState;

type SettingsFieldState = Record<SettingsField, boolean>;

const EMPTY_FORM_STATE: SettingsFormState = {
  geminiApiKey: '',
  telegramApiId: '',
  telegramApiHash: '',
  telegramSessionString: '',
  telegramBotToken: '',
};

const EMPTY_FIELD_STATE: SettingsFieldState = {
  geminiApiKey: false,
  telegramApiId: false,
  telegramApiHash: false,
  telegramSessionString: false,
  telegramBotToken: false,
};

const MASKED_VALUE = '******';

const hasStoredValue = (value: unknown) =>
  value === true || (typeof value === 'string' && value.trim() !== '');

const mapSettingsPresence = (
  settings?: UserSettings | null,
): SettingsFieldState => ({
  geminiApiKey: hasStoredValue(settings?.gemini_api_key),
  telegramApiId: hasStoredValue(settings?.telegram_api_id),
  telegramApiHash: hasStoredValue(settings?.telegram_api_hash),
  telegramSessionString: hasStoredValue(settings?.telegram_session_string),
  telegramBotToken: hasStoredValue(settings?.telegram_bot_token),
});

const mergeSettings = (
  formState: SettingsFormState,
  touchedFields: SettingsFieldState,
): UserSettings => {
  const nextSettings: UserSettings = {};

  const assignOrRemove = (
    key: keyof UserSettings,
    value: string,
  ) => {
    const trimmed = value.trim();

    if (trimmed) {
      nextSettings[key] = trimmed;
      return;
    }

    nextSettings[key] = null;
  };

  if (touchedFields.geminiApiKey) {
    assignOrRemove('gemini_api_key', formState.geminiApiKey);
  }
  if (touchedFields.telegramApiId) {
    assignOrRemove('telegram_api_id', formState.telegramApiId);
  }
  if (touchedFields.telegramApiHash) {
    assignOrRemove('telegram_api_hash', formState.telegramApiHash);
  }
  if (touchedFields.telegramSessionString) {
    assignOrRemove('telegram_session_string', formState.telegramSessionString);
  }
  if (touchedFields.telegramBotToken) {
    assignOrRemove('telegram_bot_token', formState.telegramBotToken);
  }

  return nextSettings;
};

export const SettingsPage = () => {
  const toast = useToast();
  const { data: user, isLoading, isError } = useGetCurrentUserQuery();
  const [updateCurrentUser, { isLoading: isSaving }] =
    useUpdateCurrentUserMutation();
  const [formState, setFormState] = useState<SettingsFormState>(EMPTY_FORM_STATE);
  const [storedFields, setStoredFields] =
    useState<SettingsFieldState>(EMPTY_FIELD_STATE);
  const [touchedFields, setTouchedFields] =
    useState<SettingsFieldState>(EMPTY_FIELD_STATE);

  useEffect(() => {
    if (!user) {
      return;
    }

    setFormState(EMPTY_FORM_STATE);
    setStoredFields(mapSettingsPresence(user.settings));
    setTouchedFields(EMPTY_FIELD_STATE);
  }, [user]);

  const isDirty = Object.values(touchedFields).some(Boolean);

  const handleChange = (
    field: keyof SettingsFormState,
    value: string,
  ) => {
    setTouchedFields((current) => ({
      ...current,
      [field]: true,
    }));
    setFormState((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const getDisplayValue = (field: SettingsField) => {
    if (!touchedFields[field] && storedFields[field]) {
      return MASKED_VALUE;
    }

    return formState[field];
  };

  const handleSave = async () => {
    if (!user) {
      return;
    }

    try {
      await updateCurrentUser({
        settings: mergeSettings(formState, touchedFields),
      }).unwrap();

      toast({
        title: 'Settings saved',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    } catch (error: any) {
      toast({
        title: 'Failed to save settings',
        description: error?.status === 422
          ? 'Invalid settings data'
          : 'Please try again',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  if (isLoading) {
    return (
      <Center h="400px">
        <Spinner size="xl" />
      </Center>
    );
  }

  if (isError || !user) {
    return (
      <Alert status="error" borderRadius="md">
        <AlertIcon />
        <AlertDescription>
          Unable to load your settings.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Box maxW="3xl">
      <VStack spacing={6} align="stretch">
        <Box>
          <Heading size="lg" mb={2}>
            Settings
          </Heading>
          <Text color="gray.600">
            Store personal AI and Telegram credentials in your account settings.
          </Text>
        </Box>

        <Alert status="info" borderRadius="md">
          <AlertIcon />
          <AlertDescription>
            These values are saved in your user settings object and stay attached
            to your account.
          </AlertDescription>
        </Alert>

        <Box bg="white" borderRadius="lg" boxShadow="sm" p={6}>
          <VStack spacing={5} align="stretch">
            <FormControl>
              <FormLabel>Gemini API Key</FormLabel>
              <Input
                type="password"
                value={getDisplayValue('geminiApiKey')}
                onChange={(e) => handleChange('geminiApiKey', e.target.value)}
                onFocus={(e) => {
                  if (!touchedFields.geminiApiKey && storedFields.geminiApiKey) {
                    e.target.select();
                  }
                }}
                placeholder="Enter your Gemini API key"
              />
            </FormControl>

            <FormControl>
              <FormLabel>Telegram API ID</FormLabel>
              <Input
                value={getDisplayValue('telegramApiId')}
                onChange={(e) => handleChange('telegramApiId', e.target.value)}
                onFocus={(e) => {
                  if (!touchedFields.telegramApiId && storedFields.telegramApiId) {
                    e.target.select();
                  }
                }}
                placeholder="Enter your Telegram API ID"
              />
            </FormControl>

            <FormControl>
              <FormLabel>Telegram API Hash</FormLabel>
              <Input
                type="password"
                value={getDisplayValue('telegramApiHash')}
                onChange={(e) => handleChange('telegramApiHash', e.target.value)}
                onFocus={(e) => {
                  if (
                    !touchedFields.telegramApiHash
                    && storedFields.telegramApiHash
                  ) {
                    e.target.select();
                  }
                }}
                placeholder="Enter your Telegram API hash"
              />
            </FormControl>

            <FormControl>
              <FormLabel>Telegram Session String</FormLabel>
              <Textarea
                value={getDisplayValue('telegramSessionString')}
                onChange={(e) =>
                  handleChange('telegramSessionString', e.target.value)
                }
                onFocus={(e) => {
                  if (
                    !touchedFields.telegramSessionString
                    && storedFields.telegramSessionString
                  ) {
                    e.target.select();
                  }
                }}
                placeholder="Enter your Telegram session string"
                rows={6}
              />
            </FormControl>

            <FormControl>
              <FormLabel>Telegram Bot Token</FormLabel>
              <Input
                type="password"
                value={getDisplayValue('telegramBotToken')}
                onChange={(e) =>
                  handleChange('telegramBotToken', e.target.value)
                }
                onFocus={(e) => {
                  if (
                    !touchedFields.telegramBotToken
                    && storedFields.telegramBotToken
                  ) {
                    e.target.select();
                  }
                }}
                placeholder="Enter your Telegram bot token"
              />
            </FormControl>

            <Button
              alignSelf="flex-start"
              colorScheme="blue"
              onClick={handleSave}
              isLoading={isSaving}
              isDisabled={!isDirty}
            >
              Save settings
            </Button>
          </VStack>
        </Box>
      </VStack>
    </Box>
  );
};
