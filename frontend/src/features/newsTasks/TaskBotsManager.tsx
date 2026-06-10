import {
  Box,
  Button,
  HStack,
  IconButton,
  Select,
  Text,
  VStack,
  useToast,
} from '@chakra-ui/react';
import { CloseIcon } from '@chakra-ui/icons';
import { useMemo, useState } from 'react';
import {
  useAssociateTelegramBotWithTaskMutation,
  useDisassociateTelegramBotFromTaskMutation,
  useGetCurrentUserQuery,
  useGetTaskTelegramBotsQuery,
} from '../../services/api';

interface TaskBotsManagerProps {
  taskId: string;
}

export const TaskBotsManager = ({ taskId }: TaskBotsManagerProps) => {
  const toast = useToast();
  const { data: user } = useGetCurrentUserQuery();
  const { data: associations } = useGetTaskTelegramBotsQuery(taskId);
  const [associateBot, { isLoading: isAssociating }] =
    useAssociateTelegramBotWithTaskMutation();
  const [disassociateBot, { isLoading: isDisassociating }] =
    useDisassociateTelegramBotFromTaskMutation();

  const [selectedBotId, setSelectedBotId] = useState('');

  const availableBots = user?.settings.telegram_bots ?? [];
  const associatedBotIds = useMemo(
    () => new Set((associations ?? []).map((a) => a.telegram_bot_id)),
    [associations],
  );

  const associatedBots = availableBots.filter((bot) =>
    associatedBotIds.has(bot.id),
  );

  const selectableBots = availableBots.filter(
    (bot) => !associatedBotIds.has(bot.id),
  );

  const handleAdd = async () => {
    if (!selectedBotId) {
      return;
    }

    try {
      await associateBot({
        taskId,
        botId: Number(selectedBotId),
      }).unwrap();
      setSelectedBotId('');
      toast({
        title: 'Bot added to task',
        status: 'success',
        duration: 2000,
      });
    } catch {
      toast({
        title: 'Failed to add bot',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const handleRemove = async (botId: number) => {
    try {
      await disassociateBot({ taskId, botId }).unwrap();
      toast({
        title: 'Bot removed from task',
        status: 'success',
        duration: 2000,
      });
    } catch {
      toast({
        title: 'Failed to remove bot',
        status: 'error',
        duration: 3000,
      });
    }
  };

  return (
    <VStack align="stretch" spacing={3}>
      <HStack>
        <Select
          placeholder={
            selectableBots.length > 0
              ? 'Choose a Telegram bot'
              : 'No available bots'
          }
          value={selectedBotId}
          onChange={(e) => setSelectedBotId(e.target.value)}
          isDisabled={selectableBots.length === 0 || isAssociating}
        >
          {selectableBots.map((bot) => (
            <option key={bot.id} value={String(bot.id)}>
              @{bot.bot_name} ({bot.bot_tg_id})
            </option>
          ))}
        </Select>
        <Button
          onClick={handleAdd}
          isLoading={isAssociating}
          isDisabled={!selectedBotId}
          size="sm"
          colorScheme="blue"
        >
          Add
        </Button>
      </HStack>

      {associatedBots.length === 0 ? (
        <Box p={4} bg="gray.50" borderRadius="md" textAlign="center">
          <Text fontSize="sm" color="gray.500">
            No Telegram bots assigned to this task
          </Text>
        </Box>
      ) : (
        <VStack align="stretch" spacing={2}>
          {associatedBots.map((bot) => (
            <Box
              key={bot.id}
              p={3}
              bg="gray.50"
              borderRadius="md"
              borderWidth="1px"
              borderColor="gray.200"
            >
              <HStack justify="space-between">
                <Box>
                  <Text fontWeight="medium" fontSize="sm">
                    @{bot.bot_name}
                  </Text>
                  <Text fontSize="xs" color="gray.500">
                    Telegram ID: {bot.bot_tg_id}
                  </Text>
                </Box>
                <IconButton
                  aria-label="Remove bot"
                  icon={<CloseIcon />}
                  size="xs"
                  variant="ghost"
                  colorScheme="red"
                  onClick={() => handleRemove(bot.id)}
                  isLoading={isDisassociating}
                />
              </HStack>
            </Box>
          ))}
        </VStack>
      )}
    </VStack>
  );
};
