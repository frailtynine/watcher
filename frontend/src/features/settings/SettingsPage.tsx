import { useEffect, useRef, useState } from 'react';
import {
  Alert,
  AlertDialog,
  AlertDialogBody,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogOverlay,
  AlertDescription,
  AlertIcon,
  Box,
  Button,
  Center,
  Divider,
  FormControl,
  FormErrorMessage,
  FormHelperText,
  FormLabel,
  Heading,
  Input,
  Spinner,
  Text,
  Textarea,
  VStack,
  useDisclosure,
  useToast,
} from '@chakra-ui/react';
import {
  useCreateTelegramBotMutation,
  useDeleteTelegramBotMutation,
  useGetCurrentUserQuery,
  useUpdateCurrentUserMutation,
} from '../../services/api';
import type { UserSettings, UserSettingsUpdate } from '../../types';

interface SettingsFormState {
  geminiApiKey: string;
  telegramApiId: string;
  telegramApiHash: string;
  telegramSessionString: string;
}

type SettingsField = keyof SettingsFormState;
type SettingsFieldState = Record<SettingsField, boolean>;

const EMPTY_FORM_STATE: SettingsFormState = {
  geminiApiKey: '',
  telegramApiId: '',
  telegramApiHash: '',
  telegramSessionString: '',
};

const EMPTY_FIELD_STATE: SettingsFieldState = {
  geminiApiKey: false,
  telegramApiId: false,
  telegramApiHash: false,
  telegramSessionString: false,
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
});

const mergeSettings = (
  formState: SettingsFormState,
  touchedFields: SettingsFieldState,
): UserSettingsUpdate => {
  const nextSettings: UserSettingsUpdate = {};

  const assignOrRemove = (key: keyof UserSettingsUpdate, value: string) => {
    const trimmed = value.trim();
    nextSettings[key] = trimmed || null;
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

  return nextSettings;
};

const extractErrorMessage = (error: unknown): string => {
  if (!error || typeof error !== 'object') {
    return 'Please try again';
  }

  if ('status' in error && (error.status === 422 || error.status === 400 || error.status === 409)) {
    const data = 'data' in error ? error.data : undefined;

    if (typeof data === 'string' && data.trim()) {
      return data;
    }

    if (data && typeof data === 'object' && 'detail' in data) {
      const detail = data.detail;

      if (typeof detail === 'string' && detail.trim()) {
        return detail;
      }
    }

    return 'Invalid settings data';
  }

  return 'Please try again';
};

export const SettingsPage = () => {
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const cancelRef = useRef<HTMLButtonElement>(null);
  const { data: user, isLoading, isError } = useGetCurrentUserQuery();
  const [updateCurrentUser, { isLoading: isSaving }] =
    useUpdateCurrentUserMutation();
  const [createTelegramBot, { isLoading: isCreatingBot }] =
    useCreateTelegramBotMutation();
  const [deleteTelegramBot, { isLoading: isDeletingBot }] =
    useDeleteTelegramBotMutation();

  const [formState, setFormState] = useState<SettingsFormState>(EMPTY_FORM_STATE);
  const [storedFields, setStoredFields] =
    useState<SettingsFieldState>(EMPTY_FIELD_STATE);
  const [touchedFields, setTouchedFields] =
    useState<SettingsFieldState>(EMPTY_FIELD_STATE);
  const [botToken, setBotToken] = useState('');
  const [botTokenError, setBotTokenError] = useState<string | null>(null);
  const [botToDelete, setBotToDelete] = useState<{ id: number; name: string } | null>(null);

  useEffect(() => {
    if (!user) {
      return;
    }

    setFormState(EMPTY_FORM_STATE);
    setStoredFields(mapSettingsPresence(user.settings));
    setTouchedFields(EMPTY_FIELD_STATE);
    setBotToken('');
    setBotTokenError(null);
  }, [user]);

  const handleChange = (field: SettingsField, value: string) => {
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

  const isDirty = Object.values(touchedFields).some(Boolean);

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
    } catch (error: unknown) {
      toast({
        title: 'Failed to save settings',
        description: extractErrorMessage(error),
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleAddBot = async () => {
    const token = botToken.trim();
    if (!token) {
      setBotTokenError('Bot token is required');
      return;
    }

    try {
      await createTelegramBot({ bot_token: token }).unwrap();
      setBotToken('');
      setBotTokenError(null);
      toast({
        title: 'Telegram bot added',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    } catch (error: unknown) {
      setBotTokenError(extractErrorMessage(error));
    }
  };

  const requestDeleteBot = (botId: number, botName: string) => {
    setBotToDelete({ id: botId, name: botName });
    onOpen();
  };

  const handleDeleteBot = async () => {
    if (!botToDelete) {
      return;
    }

    try {
      await deleteTelegramBot(botToDelete.id).unwrap();
      onClose();
      setBotToDelete(null);
      toast({
        title: 'Telegram bot deleted',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    } catch (error: unknown) {
      toast({
        title: 'Failed to delete bot',
        description: extractErrorMessage(error),
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleCloseDeleteDialog = () => {
    if (isDeletingBot) {
      return;
    }
    onClose();
    setBotToDelete(null);
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
    <Box maxW="4xl">
      <VStack spacing={6} align="stretch">
        <Box>
          <Heading size="lg" mb={2}>
            Settings
          </Heading>
          <Text color="gray.600">
            Manage the personal credentials NewsWatcher uses for AI
            processing and Telegram delivery.
          </Text>
        </Box>

        <Alert status="info" borderRadius="md">
          <AlertIcon />
          <AlertDescription>
            Secret values are masked after saving. Leave a masked value
            unchanged to keep it, or replace it with a new one.
          </AlertDescription>
        </Alert>

        <Box bg="white" borderRadius="lg" boxShadow="sm" p={6}>
          <VStack spacing={5} align="stretch">
            <Heading size="md">AI Settings</Heading>

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
          </VStack>
        </Box>

        <Box bg="white" borderRadius="lg" boxShadow="sm" p={6}>
          <VStack spacing={5} align="stretch">
            <Heading size="md">Telegram Producer Credentials</Heading>

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
          </VStack>
        </Box>

        <Box bg="white" borderRadius="lg" boxShadow="sm" p={6}>
          <VStack spacing={5} align="stretch">
            <Box>
              <Heading size="md" mb={1}>
                Telegram Delivery Bots
              </Heading>
              <Text color="gray.600" fontSize="sm">
                Add bot tokens. Bot name and Telegram ID are fetched and saved automatically.
              </Text>
            </Box>

            <Divider />

            <FormControl isInvalid={Boolean(botTokenError)}>
              <FormLabel>Bot Token</FormLabel>
              <Input
                type="password"
                value={botToken}
                onChange={(e) => {
                  setBotToken(e.target.value);
                  setBotTokenError(null);
                }}
                placeholder="Enter the Telegram bot token"
              />
              <FormHelperText>
                This validates the token with Telegram and stores the bot in the database.
              </FormHelperText>
              <FormErrorMessage>{botTokenError}</FormErrorMessage>
            </FormControl>

            <Button
              alignSelf="flex-start"
              variant="outline"
              onClick={handleAddBot}
              isLoading={isCreatingBot}
            >
              Add Bot
            </Button>

            <VStack align="stretch" spacing={2}>
              {(user.settings.telegram_bots ?? []).map((bot) => (
                <Box key={bot.id} borderWidth="1px" borderRadius="md" p={3}>
                  <Box display="flex" alignItems="center" justifyContent="space-between" gap={3}>
                    <Box>
                      <Text fontWeight="semibold">@{bot.bot_name}</Text>
                      <Text fontSize="sm" color="gray.600">
                        Telegram ID: {bot.bot_tg_id}
                      </Text>
                    </Box>
                    <Button
                      size="sm"
                      colorScheme="red"
                      variant="ghost"
                      onClick={() => requestDeleteBot(bot.id, bot.bot_name)}
                      isLoading={isDeletingBot && botToDelete?.id === bot.id}
                    >
                      Delete
                    </Button>
                  </Box>
                </Box>
              ))}
              {(user.settings.telegram_bots ?? []).length === 0 ? (
                <Text color="gray.500" fontSize="sm">
                  No Telegram bots configured.
                </Text>
              ) : null}
            </VStack>
          </VStack>
        </Box>

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

      <AlertDialog
        isOpen={isOpen}
        leastDestructiveRef={cancelRef}
        onClose={handleCloseDeleteDialog}
      >
        <AlertDialogOverlay>
          <AlertDialogContent>
            <AlertDialogHeader fontSize="lg" fontWeight="bold">
              Delete Telegram Bot
            </AlertDialogHeader>

            <AlertDialogBody>
              Delete @{botToDelete?.name}? This action cannot be undone.
            </AlertDialogBody>

            <AlertDialogFooter>
              <Button
                ref={cancelRef}
                onClick={handleCloseDeleteDialog}
                isDisabled={isDeletingBot}
              >
                Cancel
              </Button>
              <Button
                colorScheme="red"
                onClick={handleDeleteBot}
                ml={3}
                isLoading={isDeletingBot}
              >
                Delete
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    </Box>
  );
};
